from asyncio import streams
import csv
import gzip
import os
import requests
import tempfile
from turtle import reset
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction,connection
from django.conf import settings
from main.models import City

@contextmanager
def tempdir():
    d = tempfile.TemporaryDirectory()
    try:
        yield d.name
    finally:
        d.cleanup()
        
        
class Command(BaseCommand):
    help = "Descarga un .csv.gz, lo descomprime y carga los datos a la BD."
    
    def handle(self, *args, **options):
        url = f"{settings.BULK_CITY_LIST_URL}{settings.CITY_LIST_FILE}"
        filename = settings.CITY_LIST_FILE
        timeout = 120
        
        self.stdout.write(self.style.NOTICE(f"Descargando : {url}"))
        
        
        with tempdir() as workdir:
            gz_path = os.path.join(workdir,filename)
            json_path = os.path.join(workdir,"city.list.json")
            
            with requests.get(url,stream=True,timeout=timeout) as r:
                try:
                    r.raise_for_status()
                except Exception as e:
                    raise CommandError(f"Error al descargar {e}")
                with open(gz_path,"wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 *  1024):
                        if chunk:
                            f.write(chunk)
                            
            self.stdout.write(self.style.SUCCESS(f"Descarga completa -> {gz_path}"))
            
            with gzip.open(gz_path,"rb") as f_in,open(json_path,"wb") as f_out:
                for chunk in iter(lambda:f_in.read(1024 * 1024), b""):
                    f_out.write(chunk)
            
            self.stdout.write(self.style.SUCCESS(f"Descompresión completa -> {json_path}"))
        

            self.load_data(json_path)
    
    def _flush_batch(model_batch, batch_size):
        pass
    
    def _map_json_to_sale(obj):
        pass
    
    def load_data(json_path,batch_size=20000, encoding="utf-8"):
        
        with open(json_path, "r", encoding=encoding) as f:
            head = f.read(1)
            is_array = head == "["
            f.seek(0)
            
        print(is_array)