import struct
import datetime
import logging
import math
from typing import Optional, Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %message)s')


def convert_filetime_to_datetime(filetime_ticks: int) -> Optional[datetime.datetime]:
    """
    Converteix un FILETIME (ticks, intervals de 100 ns des del 1/1/1601) a un objecte datetime UTC.
    Si el càlcul resulta en un valor fora del rang, retorna None.
    """
    offset = 116444736000000000
    try:
        seconds = (filetime_ticks - offset) / 10000000
        if seconds < 0:
            logging.warning(f"Timestamp {filetime_ticks} resultant en un valor negatiu de segons.")
            return None
        return datetime.datetime.utcfromtimestamp(seconds)
    except Exception as e:
        logging.error(f"Error convertint timestamp {filetime_ticks}: {e}")
        return None


def llegir_header_datafile(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Llegeix la capçalera 'DATAFILEHEADER' d'un fitxer binari *.0xx amb l'estructura revisada.
    
    Args:
        file_path (str): La ruta al fitxer *.0xx.
    
    Returns:
        dict: Diccionari amb els camps de la capçalera o None si hi ha error.
    """
    try:
        with open(file_path, 'rb') as f:
            header_bytes = f.read(304)
            format_string = "<112s4f8sHHq12x80sIHHHI8sIQQIIq6x"
            unpacked = struct.unpack(format_string, header_bytes)
            header_data = {
                "Title": unpacked[0].decode('latin-1').strip('\x00'),
                "scales": {
                    "RawZero": unpacked[1],
                    "RawFull": unpacked[2],
                    "EngZero": unpacked[3],
                    "EngFull": unpacked[4]
                },
                "header": {
                    "ID": unpacked[5].decode('latin-1').strip('\x00'),
                    "Type": unpacked[6],
                    "Version": unpacked[7],
                    "StartEvNo": unpacked[8],
                    "LogName": unpacked[9].decode('latin-1').strip('\x00'),
                    "Mode": unpacked[10],
                    "Area": unpacked[11],
                    "Priv": unpacked[12],
                    "FileType": unpacked[13],
                    "SamplePeriod": unpacked[14],
                    "sEngUnits": unpacked[15].decode('latin-1').strip('\x00'),
                    "Format": unpacked[16],
                    "StartTime": unpacked[17],
                    "EndTime": unpacked[18],
                    "DataLength": unpacked[19],
                    "FilePointer": unpacked[20],
                    "EndEvNo": unpacked[21]
                }
            }
            return header_data
    except Exception as e:
        logging.error(f"Error al llegir la capçalera: {e}")
        return None


def llegir_dades(file_path: str, header_info: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Llegeix les dades del fitxer a partir de la capçalera.
    
    Args:
        file_path (str): Ruta al fitxer.
        header_info (dict): Diccionari amb les dades de la capçalera.
    
    Returns:
        list: Llista de diccionaris amb 'value' i 'time', o None en cas d'error.
    """
    try:
        with open(file_path, 'rb') as f:
            f.seek(304)
            n_samples = header_info['header']['DataLength']
            samples: List[Dict[str, Any]] = []
            sample_format = "<d"
            sample_size = struct.calcsize(sample_format)
            start_dt = convert_filetime_to_datetime(header_info['header']['StartTime'])
            if start_dt is None:
                logging.error("StartTime convertit a datetime és None.")
                return None
            delta = datetime.timedelta(milliseconds=header_info['header']['SamplePeriod'])
            nan_count = 0  # Comptador de NaN
            for i in range(n_samples):
                sample_bytes = f.read(sample_size)
                if len(sample_bytes) != sample_size:
                    logging.warning(f"Alerta: bytes insuficients a la mostra {i}")
                    break
                value = struct.unpack(sample_format, sample_bytes)[0]
                
                # Control per si el valor és NaN  
                if math.isnan(value):
                    nan_count += 1
                    continue

                value = round(value, 3)
                sample_time = start_dt + i * delta
                # Mantenim sample_time com a datetime
                samples.append({"value": value, "time": sample_time})
            if nan_count:
                logging.debug(f"NaN sample values descartats: {nan_count}")
            return samples
    except Exception as e:
        logging.error(f"Error al llegir les dades: {e}")
        return None

