# Exportador de CSV per Dades Citect

Aquest projecte és una eina desenvolupada amb Python que permet llegir fitxers de dades en format binari (amb extensió numèrica) generats per Citect, agrupar les mostres segons un període d'exportació seleccionat i exportar els resultats a arxius CSV.

## Contingut del Projecte

- **main_gui.py**  
  Script principal que implementa una interfície gràfica (GUI) amb CustomTkinter. Permet:
  - Seleccionar una carpeta d'origen que contingui subcarpetes amb dades.
  - Filtrar i seleccionar una o més subcarpetes per exportar.
  - Escollir el període d'exportació (per exemple, `20 segons`, `1 minut`, `10 minuts`, etc.) amb un selector (CTkOptionMenu) que determina la agrupació de les mostres.
  - Visualitzar el progrés de l'exportació amb una progress bar.
  - Exportar els fitxers CSV amb dades agregades (mitjana de les mostres per bucket).

- **Llegir_Fitxer_Dades.py**  
  Mòdul que conté funcions per:
  - Llegir la capçalera (`llegir_header_datafile`) d'un fitxer binari per extreure informació rellevant com el període de mostreig, timings i altres metadades.
  - Llegir les dades (`llegir_dades`) del fitxer binari, convertint timestamps basats en FILETIME a objectes `datetime`. També gestiona els valors NaN descartant-los.

## Funcionament del Procés

1. **Selecció de Carpeta d'Origen**  
   A través de la GUI, l'usuari selecciona una carpeta d'origen que ha de contenir subcarpetes amb el nom `TR2` o algun patró similar.

2. **Filtrat i Selecció de Subcarpetes**  
   El widget `FilterableItemFrame` mostra la llista de subcarpetes, permetent a l'usuari filtrar per text i seleccionar les subcarpetes a exportar.

3. **Selecció del Període d'Exportació**  
   Un CTkOptionMenu permet escollir entre diversos intervals d'exportació (ex. `20 segons`, `1 minut`, ...). Aquest espectre determina la durada del bucket per agrupar les mostres.  
   *Exemple:* Si s'escull "1 minut" i les dades originals es mostregen cada 20 segons, es prendran les tres mostres del minut (00, 20 i 40 segons) i es calcul·larà la mitjana.

4. **Lectura i Agrupació de Mostres**  
   Per cada fitxer de dades dins de les subcarpetes seleccionades:
   - Es llegeix la capçalera per obtenir metadades (només si es pot llegir correctament).
   - Es llegeixen les dades canviant el valor de cada mostra i el seu timestamp.
   - Es descarten les mostres que tinguin un valor NaN.
   - Les mostres es processen per agrupar-les en buckets de temps segons el període escollit. Es calcula la mitjana aritmètica de cada bucket.

5. **Exportació a CSV**  
   Les dades agregades es guarden en arxius CSV (un per cada subcarpeta processada). Cada fitxer CSV conté dues columnes:
   - **Time:** Temps del bucket (formatat a `dd/mm/YYYY HH:MM:SS`).
   - **Value:** Valor mitjà calculat per a aquest bucket.

6. **Feedback i Registre**  
   La GUI mostra un àrea de log on es registren missatges informatius sobre:
   - L'estat de la càrrega de la carpeta d'origen.
   - Errors en llegir fitxers o capçaleres.
   - Progrés de l'exportació.
   - Missatges de confirmació en finalitzar l'exportació.

## Requisits

- Python 3.x
- Llibreries:
  - `customtkinter` (per la GUI moderna amb Tkinter)
  - `tkinter` (inclòs amb la instal·lació estàndard de Python)
  - `struct`, `datetime`, `os`, `csv`, `logging`, `math`
  
Pots instal·lar `customtkinter` (si no el tens) amb el següent comandament:
```bash
pip install customtkinter
