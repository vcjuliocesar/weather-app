# main/management/commands/load_cities_json_gz.py

import json
import gzip
import os
import tempfile
from contextlib import contextmanager

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from main.models import City

# Opcional (recomendado para JSON enormes): pip install ijson
try:
    import ijson  # streaming parser
    HAS_IJSON = True
except Exception:
    HAS_IJSON = False


@contextmanager
def tempdir():
    d = tempfile.TemporaryDirectory()
    try:
        yield d.name
    finally:
        d.cleanup()


class Command(BaseCommand):
    help = "Descarga un .json.gz, lo descomprime y carga ciudades a la BD."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=20_000,
                            help="Tamaño de lote para bulk_create.")
        parser.add_argument("--timeout", type=int, default=120,
                            help="Timeout para la descarga en segundos.")
        parser.add_argument("--encoding", default="utf-8",
                            help="Encoding del JSON (default: utf-8).")

    def handle(self, *args, **opts):
        url = f"{settings.BULK_CITY_LIST_URL}{settings.CITY_LIST_FILE}"
        filename = settings.CITY_LIST_FILE  # e.g. 'city.list.json.gz'
        timeout = opts["timeout"]
        encoding = opts["encoding"]
        batch_size = opts["batch_size"]

        self.stdout.write(self.style.NOTICE(f"Descargando: {url}"))

        with tempdir() as workdir:
            gz_path = os.path.join(workdir, filename)
            
            json_path = os.path.join(workdir, "cities.json")

            # 1) Descargar el .gz por streaming
            with requests.get(url, stream=True, timeout=timeout) as r:
                try:
                    r.raise_for_status()
                except Exception as e:
                    raise CommandError(f"Error al descargar: {e}")
                with open(gz_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            self.stdout.write(self.style.SUCCESS(f"Descarga completa -> {gz_path}"))

            # 2) Descomprimir a JSON (sin cargar todo en RAM)
            with gzip.open(gz_path, "rb") as f_in, open(json_path, "wb") as f_out:
                for chunk in iter(lambda: f_in.read(1024 * 1024), b""):
                    f_out.write(chunk)

            self.stdout.write(self.style.SUCCESS(f"Descompresión completa -> {json_path}"))

            # 3) Detectar formato: arreglo JSON vs NDJSON
            is_array = self._looks_like_array(json_path, encoding=encoding)
            self.stdout.write(self.style.NOTICE(f"Formato detectado: {'arreglo JSON' if is_array else 'NDJSON'}"))

            # 4) Cargar datos
            inserted = self._load_data(json_path, is_array, batch_size, encoding)
            self.stdout.write(self.style.SUCCESS(f"Filas insertadas (aprox): {inserted}"))

    # -----------------------
    # Utilidades de parsing
    # -----------------------
    def _looks_like_array(self, json_path, encoding="utf-8"):
        """ Devuelve True si el archivo comienza con '[' (arreglo JSON). """
        with open(json_path, "r", encoding=encoding) as f:
            head = f.read(1)
            return head.strip() == "["

    def _map_json_to_city(self, obj):
        # Tolerancia a claves ausentes
        coord = obj.get("coord") or {}
        return City(
            name=obj.get("name") or "",
            country=obj.get("country") or "",
            lat=coord.get("lat"),
            lon=coord.get("lon"),
        )

    def _load_data(self, json_path, is_array, batch_size=20_000, encoding="utf-8"):
        """
        Inserta en lotes con bulk_create.
        - Si is_array: intenta usar ijson (streaming). Si no está disponible, hace json.load (requiere RAM).
        - Si NDJSON: parsea línea por línea.
        """
        created = 0
        buffer = []

        def flush():
            nonlocal created, buffer
            if not buffer:
                return
            with transaction.atomic():
                # Si external_id es PK única, puedes usar ignore_conflicts=True para saltar duplicados
                City.objects.bulk_create(buffer, batch_size=batch_size, ignore_conflicts=True)
            created += len(buffer)
            buffer = []

        if is_array:
            if HAS_IJSON:
                # Streaming: no se carga todo a memoria
                with open(json_path, "r", encoding=encoding) as f:
                    for obj in ijson.items(f, "item"):
                        try:
                            city = self._map_json_to_city(obj)
                            buffer.append(city)
                            if len(buffer) >= batch_size:
                                flush()
                        except Exception as e:
                            # Log de bad row; evita romper toda la carga
                            self.stderr.write(f"Objeto inválido: {e}")
                flush()
            else:
                # Fallback (memoria): solo si el archivo no es gigante
                self.stdout.write(self.style.WARNING(
                    "ijson no está instalado; usando json.load (puede usar mucha RAM)."
                ))
                with open(json_path, "r", encoding=encoding) as f:
                    data = json.load(f)
                    for obj in data:
                        try:
                            city = self._map_json_to_city(obj)
                            buffer.append(city)
                            if len(buffer) >= batch_size:
                                flush()
                        except Exception as e:
                            self.stderr.write(f"Objeto inválido: {e}")
                flush()
        else:
            # NDJSON: una línea = 1 objeto JSON
            with open(json_path, "r", encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        city = self._map_json_to_city(obj)
                        buffer.append(city)
                        if len(buffer) >= batch_size:
                            flush()
                    except Exception as e:
                        self.stderr.write(f"Línea inválida: {e}")
            flush()

        return created
