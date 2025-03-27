import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from collections import OrderedDict
import requests
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Working directory
wd= r"C:\Users\s265626\Downloads\genotox_db_2"

# Constants for file paths 
DEEPAMES_FILE = f"{wd}/myproject/media/DeepAmes.xlsx"  # Update with your actual path
HANSEN_FILE = f"{wd}/myproject/media/Hansen Data Set_Mutagenicity_N6512.xls"  # Update with your actual path
OECD_VIVO_FILE = f"{wd}/myproject/media/OECD_vivogentox.xls" # Update if needed.
OECD_CHROMOSOME_FILE = f"{wd}/myproject/media/OECD_invitro_chromosome_3.xls"
IARC_FILE = f"{wd}/myproject/media/IARC_carcinogen.xlsx"
CCRIS_FILE = f"{wd}/myproject/media/edit_CCRIS_allmutagenicity.xlsx"
AMESCEBS_FILE= f"{wd}/myproject/media/20241216-ames.csv"

OPENFOODTOX_EFSA_OUPUTS_FILE = f"{wd}/myproject/media/EFSAOutputs_KJ_2022.xlsx"
OPENFOODTOX_GENOTOX_FILE = f"{wd}/myproject/media/Genotoxicity_KJ_2022.xlsx"
OPENFOODTOX_REFPOINT_FILE = f"{wd}/myproject/media/ReferencePoints_KJ_2022.xlsx"
OPENFOODTOX_REFVALUE_FILE = f"{wd}/myproject/media/ReferenceValues_KJ_2022.xlsx"
OPENFOODTOX_SUBSTCHARACT_FILE = f"{wd}/myproject/media/SubstanceCharacterisation_KJ_2022.xlsx"

PPRTV_FILE=f"{wd}/myproject/media/pprtv_RfC_RfD_edit.xlsx"
IRIS_FILE=f"{wd}/myproject/media/simple_list_alpha.xlsx"


HOMNA_183=f"{wd}/myproject/media/ClassA183 (1).xlsx"
HOMNA_236=f"{wd}/myproject/media/ClassA236.xlsx"
HOMNA_253=f"{wd}/myproject/media/ClassA253.xlsx"

ECVAM_NEG_FILE=f"{wd}/myproject/media/ECVAM_Ames_negative_DB_2024-11-08.xlsx"
ECVAM_POS_FILE=f"{wd}/myproject/media/ECVAM_Ames_positives_DB_2024-11-08.xls"

# --- Data Loading and Cleaning Functions ---

def load_dataframe(filepath):
    """Generic function to load Excel data, handles errors and returns empty DataFrame on failure."""
    try:
        df = pd.read_excel(filepath)
        print(f"Data loaded successfully from {filepath}: {df.shape}")
        return df
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return pd.DataFrame()  # Return empty DataFrame


def clean_deepames(df):
    """Cleans and preprocesses the DeepAmes DataFrame."""
    df = df.drop(columns=['DeepAmes_Prob', 'DeepAmes_class', 'Steroid', 'WDI'], errors='ignore')
    for col in ['CAS_NO', 'Name', 'Canonical_Smiles', 'REFERENCE']:
        if col in df.columns:
            df[col] = df[col].astype(str)
    if 'Activity' in df.columns:  # Check if column exists before mapping
      df['Activity'] = df['Activity'].map({0: 'Negative', 1: 'Positive'})
    return df


def clean_hansen(df):
    """Cleans and preprocesses the Hansen DataFrame."""
    df.drop(columns=['Steroid', 'WDI'], inplace=True, errors='ignore')
    if 'Activity' in df.columns:  # Check if column exists before mapping
      df['Activity'] = df['Activity'].map({0: 'Negative', 1: 'Positive'})
    return df


def clean_oecd_vivo(df):
    """Cleans and preprocesses the OECD DataFrame."""

    #replace '\n\n\n' that separates the outcomes in 'Values' column with '\n' in order to split the column data
    df['Values'] = df['Values'].str.replace('\n\n\n','\n')
    df['Values'] = df['Values'].str.replace('\n\n','\n')


    #deletes string values repeated in each 'Values' cell
    df['Values1'] =(df['Values'].str.split('\n')
                                .apply(lambda x: OrderedDict.fromkeys(x).keys())
                                .str.join('\n'))

    #creates new column from the splitting of 'Value' columns
    df[['Type_of_information', 'Reliability', 'Endpoint','Guideline','GLP_compliance','Type_assay','Results','7','8','9','10','11','12']]=df['Values1'].str.split('\n',expand=True)

    #drops manually 'None' or useless columns such as 'Values' and 'Values1'
    df = df.drop(columns=['Values', 'Values1', '7','8','9','10','11','12'])

    return df

def clean_oecd_chromosome(df):
    """Cleans and preprocesses the OECD chromosome DataFrame."""
    df['Values'] = df['Values'].str.replace(r'\n{2,}', '\n', regex=True)
    df['Values1'] = (df['Values'].str.split('\n')
                    .apply(lambda x: OrderedDict.fromkeys(x).keys())
                    .str.join('\n'))
    split_cols = ['Type_of_information', 'Reliability', 'Endpoint', 'Guideline', 'GLP_compliance', 'Type_assay', 'Strain', 'Metabolic_activation', 'Results'] + [str(i) for i in range(9, 20)]  # Corrected range
    df[split_cols] = df['Values1'].str.split('\n', expand=True)
    df = df.drop(columns=['Values', 'Values1'] + [str(i) for i in range(9, 20)])
    return df

def clean_iarc(df):
    """Cleans and preprocesses the IARC DataFrame."""
    print(f"IARC carc: {df.loc[df.index[-1],'CAS No.']}") # Print the update info
    df.drop(df.index[-1], inplace=True) # Drop the last row (update info)
    df.rename(columns={'CAS No.': 'CAS_numb'}, inplace=True)
    df['CAS_numb'] = df['CAS_numb'].astype(str) # Ensure CAS_numb is a string
    return df


def clean_ccris(df):
    """Cleans and preprocesses the CCRIS DataFrame."""
    df.drop(columns=['PUBCHEM_RESULT_TAG', 'PUBCHEM_ACTIVITY_URL', 'PUBCHEM_ACTIVITY_SCORE', 'PUBCHEM_ASSAYDATA_COMMENT'], inplace=True, errors='ignore') # errors='ignore' in case the columns are not found
    df.drop(0, axis=0, inplace=True, errors='ignore') # errors='ignore' in case the row is not found

    for index in df.index:
        if str(df.loc[index, 'End Point']) == "Ames Salmonella typhimurium":
            df.loc[index, 'Strain/Indicator'] = df.loc[index, 'Test System']
            df.loc[index, 'Test System'] = df.loc[index, 'End Point']
            df.loc[index, 'End Point'] = None
    return df

def clean_amescebs(df):
    """Cleans and preprocesses the AMESCEBS DataFrame."""
    df[['CAS_NO', 'Delete1']] = df['CASRN'].str.split('(', expand=True)
    df[['NTP_study_number', 'Delete2']] = df['NTP Study Number'].str.split('(', expand=True)

    df.drop(columns=['Delete1', 'Delete2', 'CASRN', 'NTP Study Number', 'Trial Start Date'], inplace=True, errors='ignore')  # Combine drops and handle missing columns

    df['CAS_NO'] = df['CAS_NO'].str.strip()
    return df


def clean_PPRTVIRIS(pprtv,iris):
  """Cleans and preprocesses the PPRTV and IRIS DataFrames."""

  iris.drop(columns='Unnamed: 0', inplace= True)

  pd.options.mode.copy_on_write = True

  pprtv['Last Revision']=pprtv['Last Revision'].astype(str)
  pprtv['Last Revision']=pprtv['Last Revision'].str.replace('.0','')

  iris['Last Significant Revision*']=iris['Last Significant Revision*'].astype(str)
  iris['Critical Effect Systems']=iris['Critical Effect Systems'].str.replace('\n',', ')

  return pprtv, iris



def clean_jap(df1):

  for col in df1.columns:
    if str(col).startswith('Unnamed'):
      df1.drop(col, axis=1, inplace=True)
  # Create a list of indices to drop instead of modifying the dataframe in place
  indices_to_drop = []
  for index in df1.index:
    # Access the 'Serial_Id' value for the current row using the index
    if ('Class A' in str(df1.loc[index,'Serial_Id'])) or ('Serial_Id' in str(df1.loc[index,'Serial_Id'])):
      indices_to_drop.append(index)
    else: # Only process and modify rows that are not to be dropped
      df1.loc[index,'SMILES'] = str(df1.loc[index,'SMILES']).replace('\n','')
      df1.loc[index,'CAS#'] = str(df1.loc[index,'CAS#']).replace('\n','')
      # Convert 'CAS#' to string if it exists in the DataFrame
      if 'CAS#' in df1.columns:
          df1.loc[index, 'CAS#'] = str(df1.loc[index, 'CAS#'])

  # Now drop the rows outside the loop
  df1.drop(indices_to_drop, axis=0, inplace=True)

  df1['CAS#']=df1['CAS#'].str.replace(' 00:00:00','')
  if 'Structure' in df1.columns:
    df1.drop(columns='Structure',inplace=True)

  return df1







# --- MODIFY FUNCTIONS --- #

def modify_oecd(df):
    """Modifies the OECD DataFrame to remove prefixes."""
    prefixes = {
        'Type_of_information': 'Type of information:',
        'Reliability': 'Reliability:',
        'Endpoint': 'Endpoint:',
        'Guideline': 'Guideline:',
        'GLP_compliance': 'GLP compliance:',
        'Type_assay': 'Type of assay:',
        'Strain': 'Species / strain, Species / strain:',
        'Metabolic_activation': 'Species / strain, Metabolic activation:',
        'Results': 'Test results,'
    }
    for col, prefix in prefixes.items():
        if col in df.columns: #check if the column exists
            df[col] = df[col].str.replace(prefix, '', regex=False) #regex=False for literal string replacement
    return df

def modify_activity_iarc(dt):
    """Modifies the IARC DataFrame to add activity descriptions."""
    mapping = {  # Use a dictionary for cleaner mapping
        "1": "1: Carcinogenic to humans",
        "2A": "2A: Probably carcinogenic to humans",
        "2B": "2B: Possibly carcinogenic to humans",
        "3": "3: Not classifiable as to its carcinogenicity to humans",
    }
    dt['Group'] = dt['Group'].astype(str).map(mapping).fillna(dt['Group']) # map and if the value is not found it keeps the old one
    return dt




def ccris_summary_table(dt):
    """Generates a summary table for CCRIS data."""
    summarized_data = []
    dg_list = []
    summary_call = 'N/D'

    for name, group in dt.groupby(['Test System']):
        dg1 = group
        dg_list.append(dg1)

        test_system = name  # Name is already a single value in this case
        ames_strains = ', '.join(group['Strain/Indicator'].unique().astype(str))

        positives = group['Results'].str.contains('POSITIVE', case=False).sum()
        negatives = group['Results'].str.contains('NEGATIVE', case=False).sum()
        equivocals = group['Results'].str.contains('EQUIVOCAL', case=False).sum()

        result = f"P\n/E= {positives} / {negatives} / {equivocals}"

        if positives != 0 and negatives != 0:
            summary_call = 'Conflicted'
        elif positives != 0 and negatives == 0:
            summary_call = 'Positive'
        elif negatives != 0 and positives == 0:
            summary_call = 'Negative'
        elif result == 'P\n/E= 0 / 0 / 0':
            summary_call = 'N/D'

        summarized_data.append([test_system, ames_strains, result, summary_call])

    summary_df = pd.DataFrame(summarized_data, columns=['Test System', 'Ames Strains', 'Result', 'Summary call'])
    return dg_list, summary_df


def modify_amescebs(dt):
    """Modifies the AMESCEBS DataFrame to add the '+-s9' column."""
    dt['+-s9'] = dt['Microsomal Activation Condition'].apply(lambda x: '-S9' if x == 'Without S9' else '+S9')  # More efficient using apply
    return dt

def cebs_supersummary_table(dt):
    """Generates the AMESCEBS supersummary table."""
    positives = dt['Trial Conclusion'].str.contains('Positive', case=False).sum()
    negatives = dt['Trial Conclusion'].str.contains('Negative', case=False).sum()
    equivocals = dt['Trial Conclusion'].str.contains('Equivocal', case=False).sum()

    summary_call = 'N/D'  # Default value
    if positives != 0 and negatives != 0:
        summary_call = 'Conflicted'
    elif positives != 0 and negatives == 0:
        summary_call = 'Positive'
    elif negatives != 0 and positives == 0 and equivocals == 0:
        summary_call = 'Negative'
    elif negatives != 0 and positives == 0 and equivocals != 0:
        summary_call = 'Equivocal'
    # elif result == 'P\n/E= 0 / 0 / 0':  # This condition is always false, because result is defined after this if
    #     summary_call = 'N/D' # removed this condition because it is redundant.

    result = f"{summary_call}, P\n/E= {positives} / {negatives} / {equivocals}"

    unique_strains = ', '.join(dt['Strain'].unique())

    summary_df = pd.DataFrame(data=[[unique_strains, result]],
                              columns=['Strains', 'Summary call'])

    return summary_df



def cebs_summary_table(dt):
    """Generates the AMESCEBS summary table."""
    summarized_data = []

    for (strain, s9_condition), group in dt.groupby(['Strain', '+-s9']):
        positives = group['Trial Conclusion'].str.contains('Positive', case=False).sum()
        negatives = group['Trial Conclusion'].str.contains('Negative', case=False).sum()
        equivocals = group['Trial Conclusion'].str.contains('Equivocal', case=False).sum()

        summary_call = 'N/D'
        if positives != 0 and negatives != 0:
            summary_call = 'Conflicted'
        elif positives != 0 and negatives == 0:
            summary_call = 'Positive'
        elif negatives != 0 and positives == 0 and equivocals == 0:
            summary_call = 'Negative'
        elif negatives != 0 and positives == 0 and equivocals != 0:
            summary_call = 'Equivocal'

        result = f"P\n/E= {positives} / {negatives} / {equivocals}"

        summarized_data.append([strain, s9_condition, result, summary_call])

    summary_df = pd.DataFrame(summarized_data, columns=['Test System', 'Metabolic Activation', 'Result', 'Summary call'])
    return summary_df


def genotox_openfoodtox(cas_rn,subst_name,genotox_df,outputs_df):

  dt_genotox = genotox_df[genotox_df['Substance'] == subst_name]
 # dt_genotox=genotox_df.query(f'Substance == "{subst_name}"')

  genotox_ref=pd.merge(dt_genotox, outputs_df, on=['OutputID','Substance'], how='left')
  # genotox_ref.drop(columns='URL',inplace=True)
  if not genotox_ref.empty:

    genotox_summary={}
    try:
      #generate smiles from CAS number
      extracted_row_CAS = str(cas_rn)
      smiles = cirpy.resolve(extracted_row_CAS, 'smiles')

      #getting rdkit mol object from smiles
      D_structure= Chem.MolFromSmiles(smiles)
    except:
      D_structure='No 2D structure found'
      print(f"OpenFoodTox: No smiles found for CAS_NO: {cas_rn}")

    # Calculate P\n/E counts for all strains
    positives = dt_genotox['Genotoxicity'].str.contains('Positive', case=False).sum()
    negatives = dt_genotox['Genotoxicity'].str.contains('Negative', case=False).sum()
    equivocals = dt_genotox['Genotoxicity'].str.contains('Equivocal|Ambiguous', case=False).sum()

    summary_call='N/D'
    #decide the summary call
    if positives != 0 and negatives != 0:
      summary_call= 'Conflicted'
    elif positives!=0 and negatives==0:
      summary_call= 'Positive'
    elif negatives!=0 and positives==0 and equivocals==0:
      summary_call= 'Negative'
    elif negatives!=0 and positives==0 and equivocals!=0:
      summary_call= 'Equivocal'
    elif negatives==0 and positives==0 and equivocals==0:
      summary_call= 'N/D'

    result =  f"{summary_call}, P\n/E= {positives} / {negatives} / {equivocals}"



    genotox_summary=dt_genotox.iloc[0]['Substance'],result,D_structure
    genotox_summary=pd.DataFrame(genotox_summary,index=['Substance','Summary','2D_structure'],columns=[str(cas_rn)])

    if genotox_summary.empty:
      genotox_summary=None
  else:
    genotox_summary=None
    genotox_ref=None
  return genotox_summary, genotox_ref

def refpoint_openfoodtox(subst_name,refpoint_df,outputs_df):

  dt_refpoint = refpoint_df[refpoint_df['Substance'] == subst_name]
  #dt_refpoint=refpoint_df.query(f'Substance == "{subst_name}"')

  if dt_refpoint.empty:
    refpoint_ref=None
  else:
    for index in dt_refpoint.index:
      dt_refpoint.loc[index,'refpoint']=str(f"{dt_refpoint.loc[index,'Endpoint']}{dt_refpoint.loc[index,'qualifier']}{dt_refpoint.loc[index,'value']}{dt_refpoint.loc[index,'unit']}")

    dt_refpoint.drop(columns=['Endpoint','qualifier','value','unit'], inplace=True)

    # dt_refpoint['DurationDays']=dt_refpoint['DurationDays'].astype(int)

    refpoint_ref=pd.merge(dt_refpoint,outputs_df , on=['OutputID','Substance'], how='left')

  return refpoint_ref

def refvalue_openfoodtox(subst_name,refvalue_df,outputs_df):

  dt_refvalue = refvalue_df[refvalue_df['Substance'] == subst_name]
  #dt_refvalue=refvalue_df.query(f'Substance == "{subst_name}"')

  if dt_refvalue.empty:
    refvalue_ref=None
  else:
    for index in dt_refvalue.index:
      dt_refvalue.loc[index,'Refvalue']=str(f"{dt_refvalue.loc[index,'Assessment']}{dt_refvalue.loc[index,'qualfier']}{dt_refvalue.loc[index,'value']}{dt_refvalue.loc[index,'unit']}")
    dt_refvalue.drop(columns=['Assessment','qualfier','value','unit'], inplace=True)

    refvalue_ref=pd.merge(dt_refvalue,outputs_df , on=['OutputID','Substance'], how='left')


  return refvalue_ref

def joined_table_PPRTV_IRIS(pprtv_dt,iris_dt):

    left_j=pd.merge(pprtv_dt,iris_dt, on=['CASRN'], how='left')
    # Create a list to store the multi-level column names
    new_columns = []

    # Iterate through the columns of left_j
    for col in left_j.columns:
      # If the column is in pprtv_dt, assign 'PPRTV' as the top-level header
      if col in pprtv_dt.columns:
          new_columns.append(('PPRTV', col))
      # If the column is in iris_dt, assign 'IRIS' as the top-level header
      elif col in iris_dt.columns:
          new_columns.append(('IRIS', col))
      else:  # For common columns like 'CASRN'
          new_columns.append(('', col))

    # Assign the new multi-level columns to left_j
    left_j.columns = pd.MultiIndex.from_tuples(new_columns)

    # If left_j is not empty and has the required columns
    if not left_j.empty and ('IRIS', 'Chemical Name') in left_j.columns and ('PPRTV', 'Chemical') in left_j.columns:
      for index in left_j.index:
        if str(left_j.loc[index][('IRIS', 'Chemical Name')]).lower()==str(left_j.loc[index][('PPRTV','Chemical')]).lower():
          left_j.drop(columns=('IRIS', 'Chemical Name'), inplace=True)

    left_j.dropna(axis=1, how='all', inplace=True)

    return left_j.transpose()


def add_cas_db_version_identificative(dt,cas_rn,db_file):

  """""Aggiunge righe cas_rn, nome database e versione database"""""

  diz_db_name={
      f"{wd}/myproject/media/DeepAmes.xlsx":'DeepAmes',
      f"{wd}/myproject/media/Hansen Data Set_Mutagenicity_N6512.xls":'Hansen',
      f"{wd}/myproject/media/OECD_vivogentox.xls":'OECD_VIVO',
      f"{wd}/myproject/media/OECD_invitro_chromosome_3.xls":'OECD_CHROMOSOME',
      f"{wd}/myproject/media/IARC_carcinogen.xlsx": 'IARC',
      f"{wd}/myproject/media/edit_CCRIS_allmutagenicity.xlsx": 'CCRIS',
      f"{wd}/myproject/media/20241216-ames.csv": 'AMESCEBS',
      f"{wd}/myproject/media/EFSAOutputs_KJ_2022.xlsx": 'OPFT_EFSA_OUTPUT',
      f"{wd}/myproject/media/Genotoxicity_KJ_2022.xlsx": 'OPFT_GENOTOX',
      f"{wd}/myproject/media/ReferencePoints_KJ_2022.xlsx": 'OPFT_REFPOINT',
      f"{wd}/myproject/media/ReferenceValues_KJ_2022.xlsx": 'OPFT_REFVALUE',
      f"{wd}/myproject/media/SubstanceCharacterisation_KJ_2022.xlsx": 'OPFT_SUBSTCHARACT',
      f"{wd}/myproject/media/pprtv_RfC_RfD_edit.xlsx": 'PPRTV',
      f"{wd}/myproject/media/simple_list_alpha.xlsx": 'IRIS',
      f"{wd}/myproject/media/ClassA183 (1).xlsx": 'HOMNA',
      f"{wd}/myproject/media/ClassA236.xlsx":'HOMNA',
      f"{wd}/myproject/media/ClassA253.xlsx":'HOMNA',
      f"{wd}/myproject/media/ECVAM_Ames_negative_DB_2024-11-08.xlsx":'ECVAM_NEG',
      f"{wd}/myproject/media/ECVAM_Ames_positives_DB_2024-11-08.xls":'ECVAM_POS'
  }

  diz_db_version={
      f"{wd}/myproject/media/DeepAmes.xlsx":'1.0 / 10/2023',
      f"{wd}/myproject/media/Hansen Data Set_Mutagenicity_N6512.xls":'1.0 / 09/2009',
      f"{wd}/myproject/media/OECD_vivogentox.xls":'3.0 / 2020',
      f"{wd}/myproject/media/OECD_invitro_chromosome_3.xls":'3.0 / 2020',
      f"{wd}/myproject/media/IARC_carcinogen.xlsx": '2024-09-12',
      f"{wd}/myproject/media/edit_CCRIS_allmutagenicity.xlsx": '2011',
      f"{wd}/myproject/media/20241216-ames.csv": '09/2024',
      f"{wd}/myproject/media/EFSAOutputs_KJ_2022.xlsx": '2023',
      f"{wd}/myproject/media/Genotoxicity_KJ_2022.xlsx": '2023',
      f"{wd}/myproject/media/ReferencePoints_KJ_2022.xlsx": '2023',
      f"{wd}/myproject/media/ReferenceValues_KJ_2022.xlsx": '2023',
      f"{wd}/myproject/media/SubstanceCharacterisation_KJ_2022.xlsx": '2023',
      f"{wd}/myproject/media/pprtv_RfC_RfD_edit.xlsx": '07/2024',
      f"{wd}/myproject/media/simple_list_alpha.xlsx": '07/2024',
      f"{wd}/myproject/media/ClassA183 (1).xlsx": '2018',
      f"{wd}/myproject/media/ClassA236.xlsx":'2018',
      f"{wd}/myproject/media/ClassA253.xlsx":'2018',
      f"{wd}/myproject/media/ECVAM_Ames_negative_DB_2024-11-08.xlsx":'2020',
      f"{wd}/myproject/media/ECVAM_Ames_positives_DB_2024-11-08.xls":'2020'
  }

  if dt is not None:
    dt['cas_rn'] = cas_rn
    if str(db_file) in diz_db_name:
      dt['db_name'] = diz_db_name[str(db_file)]
    if str(db_file) in diz_db_version:
      dt['db_version']= diz_db_version[str(db_file)]
  return dt




# --- Query Functions ---

def query_deepames(cas_rn):
    df = load_dataframe(DEEPAMES_FILE)
    if df.empty or"CAS_NO" not in df.columns:  #Check if df is empty or if CAS_NO exists
        return None
    df["CAS_NO"] = df["CAS_NO"].astype(str).fillna("")
    dt = df.loc[df["CAS_NO"] == cas_rn]
    dt=add_cas_db_version_identificative(dt,cas_rn,DEEPAMES_FILE)
    return clean_deepames(dt).transpose() if not dt.empty else None #combined return and transpose


def query_hansen(cas_rn):
    df = load_dataframe(HANSEN_FILE)
    if df.empty or"CAS_NO" not in df.columns: #Check if df is empty or if CAS_NO exists
        return None
    dt = df[df['CAS_NO'] == cas_rn]
    dt=add_cas_db_version_identificative(dt,cas_rn,HANSEN_FILE)
    return clean_hansen(dt).transpose() if not dt.empty else None


def query_oecd_vivo(cas_rn):
    df = load_dataframe(OECD_VIVO_FILE)
    df=clean_oecd_vivo(df)
    if df.empty or"Number" not in df.columns: #Check if df is empty or if Number exists
       return None
    dt = df[df['Number'] == cas_rn]
    dt=add_cas_db_version_identificative(dt,cas_rn,OECD_VIVO_FILE)
    return modify_oecd(dt).transpose() if not dt.empty else None

def query_oecd_chromosome(cas_rn):
    df = load_dataframe(OECD_CHROMOSOME_FILE)  # Use load_dataframe
    if df.empty or"Number" not in df.columns:
        return None
    df = clean_oecd_chromosome(df)  # Clean the DataFrame
    dt = df[df['Number'] == cas_rn]


    dt = modify_oecd(dt) # apply modifications

    if not dt.empty:
        dt=add_cas_db_version_identificative(dt,cas_rn,OECD_CHROMOSOME_FILE)
        return dt.transpose()
    else:
        return None


def query_iarc(cas_rn):
    df=pd.read_excel(IARC_FILE, header=0, skiprows=[0])  # Use load_dataframe and parameters
    if df.empty:
        return None
    else:
     df = clean_iarc(df) # clean the dataframe
     dt = df[df['CAS_numb'] == cas_rn]

     if not dt.empty:
         dt = modify_activity_iarc(dt)  # Modify activity descriptions
         dt=add_cas_db_version_identificative(dt,cas_rn,IARC_FILE)
         return dt.transpose()
     else:
         return None



def query_ccris(inchi_key,details):
    df = load_dataframe(CCRIS_FILE)  # Use load_dataframe
    if df.empty or"INCHI_key" not in df.columns:
        return None, None

    df = clean_ccris(df)
    dt = df[df['INCHI_key'] == inchi_key]

    if not dt.empty and details=='on':
        print(f"CCRIS muta: Data found for INCHI_key: {inchi_key}")

        dg, summary_df = ccris_summary_table(dt)
        return dg, summary_df
    elif not dt.empty and details!='on':
        dg, summary_df = ccris_summary_table(dt)
        return None, summary_df
    else:
        print(f"CCRIS muta: No data found for INCHI_key: {inchi_key}")
        return None, None



def query_amescebs(cas_rn,details):
    """Queries the AMESCEBS data and generates summary tables."""
    df = pd.read_csv(AMESCEBS_FILE) # Use load_dataframe
    # print(df)
    if df.empty:
        return None, None

    df = clean_amescebs(df)
    dt = df[df['CAS_NO'] == cas_rn]
    # print(dt)

    if not dt.empty and details=='on':
        print(f"AMES CEBS muta: Data found for CAS_NO: {cas_rn}")

        dt = modify_amescebs(dt)

        supersummary = cebs_supersummary_table(dt)
        summary = cebs_summary_table(dt)
        supersummary = add_cas_db_version_identificative(supersummary,cas_rn,AMESCEBS_FILE)
        summary = add_cas_db_version_identificative(summary,cas_rn,AMESCEBS_FILE)
        return summary.transpose(), supersummary.transpose()
    elif not dt.empty and details!='on':
        dt = modify_amescebs(dt)
        supersummary = cebs_supersummary_table(dt)
        supersummary = add_cas_db_version_identificative(supersummary,cas_rn,AMESCEBS_FILE)
        return None, supersummary.transpose()
    else:
        print(f"AMES CEBS muta: No data found for CAS_NO: {cas_rn}")
        return None, None

def query_openfoodtox(cas_rn):
  """Queries the Open Food Tox data."""

  outputs_df = load_dataframe(OPENFOODTOX_EFSA_OUPUTS_FILE)
  genotox_df = load_dataframe(OPENFOODTOX_GENOTOX_FILE)
  refpoint_df= load_dataframe(OPENFOODTOX_REFPOINT_FILE)
  refvalue_df= load_dataframe(OPENFOODTOX_REFVALUE_FILE)
  substcharact_df= load_dataframe(OPENFOODTOX_SUBSTCHARACT_FILE)

  # dt=substcharact_df.query(f'CASNumber == "{cas_rn}"')
  dt = substcharact_df[substcharact_df['CASNumber'] == cas_rn]

  if not dt.empty:

    outputs_df.drop(columns='URL',inplace=True)
    outputs_df['Published']=outputs_df['Published'].astype(str)
    print(f"OpenFoodTox: data found for {cas_rn}")

    subst_name=str(dt.iloc[0]['Component'])

    subst_name2=str(dt.iloc[0]['Substance'])

    # Query different tables

    genotox_summary, genotox_ref=genotox_openfoodtox(cas_rn,subst_name,genotox_df,outputs_df)
    if genotox_ref is None:
      genotox_summary, genotox_ref=genotox_openfoodtox(cas_rn,subst_name2,genotox_df,outputs_df)
    refpoint_ref=refpoint_openfoodtox(subst_name,refpoint_df,outputs_df)
    if refpoint_ref is None:
      refpoint_ref=refpoint_openfoodtox(subst_name2,refpoint_df,outputs_df)
    refvalue_ref=refvalue_openfoodtox(subst_name,refvalue_df,outputs_df)
    if refvalue_ref is None:
      refvalue_ref=refvalue_openfoodtox(subst_name2,refvalue_df,outputs_df)

    if genotox_summary is not None:
      genotox_summary = add_cas_db_version_identificative(genotox_summary.transpose(),cas_rn,OPENFOODTOX_GENOTOX_FILE).transpose()
    if genotox_ref is not None:
      genotox_ref = add_cas_db_version_identificative(genotox_ref,cas_rn,OPENFOODTOX_GENOTOX_FILE).transpose()
    if refpoint_ref is not None:
      refpoint_ref = add_cas_db_version_identificative(refpoint_ref,cas_rn,OPENFOODTOX_REFPOINT_FILE).transpose()
    if refvalue_ref is not None:
      refvalue_ref = add_cas_db_version_identificative(refvalue_ref,cas_rn,OPENFOODTOX_REFVALUE_FILE).transpose()

    return genotox_summary, genotox_ref, refpoint_ref, refvalue_ref

  else:
    print(f" OpenFoodTox: data not found for: {cas_rn}")
    return None, None, None, None
def query_PPRTV(cas_rn,pprtv):

  pprtv_dt = pprtv[pprtv['CASRN'] == cas_rn]
  # pprtv_dt=pprtv.query(f'CASRN == "{cas_rn}"')

  # Iterate through rows using .iterrows()
  for index, row in pprtv_dt.iterrows():
    # Access values using column names
    if str(row['RfC Value'])=='Not available' and str(row['RfD Value'])=='Not available':
      pprtv_dt=pprtv_dt.drop(index) # Consider using pprtv_dt = pprtv_dt.drop(index) instead if you intend to remove the row
      print('pprtv is empty')
      break # Exit the loop once the condition is met

  return pprtv_dt

def query_IRIS(cas_rn,iris):

  iris_dt = iris[iris['CASRN'] == cas_rn]
  # iris_dt=iris.query(f'CASRN == "{cas_rn}"')

  if iris_dt.empty:
    iris_dt=None


  return iris_dt


def query_IRIS_PPRTV(cas_rn):

  pprtv = load_dataframe(PPRTV_FILE)
  iris = load_dataframe(IRIS_FILE)

  #upload and clean pprtv and iris db
  pprtv,iris=clean_PPRTVIRIS(pprtv,iris)
  pd.options.mode.copy_on_write = True

  #Query both pprtv and iris db cleaned
  pprtv_dt=query_PPRTV(cas_rn,pprtv)
  pprtv_dt=add_cas_db_version_identificative(pprtv_dt,cas_rn,PPRTV_FILE)

  iris_dt=query_IRIS(cas_rn,iris)
  iris_dt=add_cas_db_version_identificative(iris_dt,cas_rn,IRIS_FILE)

  #Check if both IRIS and PPRTV are empty
  if  pprtv_dt.empty==True and iris_dt is None:
    print(f" PPRTV/IRIS: No data for {cas_rn}")
    return None

  #Check if PPRTV is empty and IRIS is not
  elif pprtv_dt.empty==True and iris_dt is not None:
    iris_dt.dropna(axis=1, how='all', inplace=True)
    print(f" PPRTV/IRIS: IRIS data found for {cas_rn}")
    return iris_dt.transpose()

  #Check if PPRTV is full and IRIS is not
  elif pprtv_dt.empty!=True and iris_dt is None:
    print(f" PPRTV data found for {cas_rn}")
    return pprtv_dt.transpose()

  #Both are full
  else:
    print(f" PPRTV/IRIS: Data found for {cas_rn}")
    dtj=joined_table_PPRTV_IRIS(pprtv_dt,iris_dt)
    #dtj=add_cas_db_version_identificative(dtj,cas_rn,PPRTV_FILE)
    return dtj

def query_homna(cas_rn):

  # read DeepAmes xlsx data
  df1=pd.read_excel(HOMNA_183, header=0, skiprows=[0])
  df2=pd.read_excel(HOMNA_236, header=0, skiprows=[0])
  df3=pd.read_excel(HOMNA_253)

  df_a=clean_jap(df1)
  df_b=clean_jap(df2)
  df_c=clean_jap(df3)

  df_final=pd.concat([df_a, df_b, df_c], ignore_index=True)
  df_final.drop_duplicates(inplace=True)
  df_final.rename(columns={'CAS#':'CAS_NO'}, inplace=True)

  jap_dt = df_final[df_final['CAS_NO'] == cas_rn]
  # jap_dt=df_final.query(f'CAS_NO == "{cas_rn}"')
  if jap_dt.empty:
    print(f"HOMNA: No data found for {cas_rn}")
    return None
  else:
    print(f"Homna data found for {cas_rn}")
    jap_dt['AMES RESULT']='Class A: Strong Positive'

    jap_dt=add_cas_db_version_identificative(jap_dt,cas_rn,HOMNA_183)
    return jap_dt.transpose()


def query_ecvam_neg(cas_rn):
    """Queries ECVAM negative data and generates summary tables and dataframes."""
    summary, df_ames, df_mcgm, df_mnvit, df_cavit, df_mnvivo, df_cavivo, df_tgr, df_uds, df_comet, df_carc, add_info, final_df = ECVAM_neg_overall(cas_rn)
    list_ecvam_neg_df=[summary, df_ames, df_mcgm, df_mnvit, df_cavit, df_mnvivo, df_cavivo, df_tgr, df_uds, df_comet, df_carc, add_info]
    for i,df in enumerate(list_ecvam_neg_df):
      if df is not None:
        df=pd.DataFrame(df)
        df=add_cas_db_version_identificative(df,cas_rn,ECVAM_NEG_FILE)
        df=df.transpose()
        list_ecvam_neg_df[i]=df
    results = {
        'ECVAM_Neg_Summary': list_ecvam_neg_df[0],
        'ECVAM_Neg_AMES': list_ecvam_neg_df[1],
        'ECVAM_Neg_MCGM': list_ecvam_neg_df[2],
        'ECVAM_Neg_MNvit': list_ecvam_neg_df[3],
        'ECVAM_Neg_CAvit': list_ecvam_neg_df[4],
        'ECVAM_Neg_MNvivo': list_ecvam_neg_df[5],
        'ECVAM_Neg_CAvivo':list_ecvam_neg_df[6],
        'ECVAM_Neg_TGR': list_ecvam_neg_df[7],
        'ECVAM_Neg_UDS': list_ecvam_neg_df[8],
        'ECVAM_Neg_COMET': list_ecvam_neg_df[9],
        'ECVAM_Neg_CARC': list_ecvam_neg_df[10],
        'ECVAM_Neg_Other_Studies':list_ecvam_neg_df[11],
        'ECVAM_Neg_References': final_df,
    }
    return results if any(value is not None for value in results.values()) else None # Return None if all values are None


def query_ecvam_pos(cas_rn, details):
    """Queries ECVAM positive data and generates summary tables and dataframes."""
    summary, ames, vit_mla, vit_mn, vit_ca, viv_mn, viv_ca, viv_uds, vivo_tgr, vivo_dna, carc, add_info, lit_table = ECVAM_pos_overall(cas_rn, details)
    list_ecvam_pos_df=[summary, ames, vit_mla, vit_mn, vit_ca, viv_mn, viv_ca, viv_uds, vivo_tgr, vivo_dna, carc, add_info, lit_table]
    for i,df in enumerate(list_ecvam_pos_df):
      if df is not None:
        df=pd.DataFrame(df)
        # print(i)
        # display(df)
        df=add_cas_db_version_identificative(df,cas_rn,ECVAM_POS_FILE)
        df=df.transpose()
        list_ecvam_pos_df[i]=df
        # display(df)
        # print("+++++++++++dopo+++++++++++++")
    # print(list_ecvam_pos_df)
    results = {
        'ECVAM_Pos_Summary': list_ecvam_pos_df[0],
        'ECVAM_Pos_AMES': list_ecvam_pos_df[1],  # Use more descriptive variable names
        'ECVAM_Pos_Vit_MLA': list_ecvam_pos_df[2],
        'ECVAM_Pos_Vit_MN': list_ecvam_pos_df[3],
        'ECVAM_Pos_Vit_CA': list_ecvam_pos_df[4],
        'ECVAM_Pos_Viv_MN': list_ecvam_pos_df[5],
        'ECVAM_Pos_Viv_CA': list_ecvam_pos_df[6],
        'ECVAM_Pos_Viv_UDS': list_ecvam_pos_df[7],
        'ECVAM_Pos_Vivo_TGR': list_ecvam_pos_df[8],  # More consistent naming
        'ECVAM_Pos_Vivo_DNA': list_ecvam_pos_df[9],  # More consistent naming
        'ECVAM_Pos_CARC': list_ecvam_pos_df[10],
        'ECVAM_Pos_Other_Studies': list_ecvam_pos_df[11],
        'ECVAM_Pos_References': list_ecvam_pos_df[12],
    }
    return results if any(value is not None for value in results.values()) else None # Return None if all values are None





# --- ECVAM NEGATIVE FUNCTIONS --- #
def ECVAM_neg_subtable(dt,keyword):
  overall_diz={'MCGM':'in vitro MCGM Overall', 'MNvit':'in vitro MN Overall', 'CAvit': 'in vitro CA  Overall', 'MNvivo': 'in vivo MN Overall', 'CAvivo': 'in vivo CA Overall','UDS ':'in vivo UDS Overall', 'COMET': ' in vivo DNA damage Overall', 'CARC': 'Rodent Carcinogenicity Overall'}

  a_list=[]
  for col in dt.columns:
    if col.startswith(str(keyword)):
      a_list.append(col)
  if str(keyword) in overall_diz: # Assuming you want to check if it's not None or empty.  Replace with appropriate check if needed.
    a_list.append(overall_diz[str(keyword)])
  a_dt=dt[a_list]
  a_dt.dropna(axis=1,inplace=True)
  if a_dt.empty:
    print(' ')
  else:
    return a_dt

def ECVAM_neg_summary_table(dt,cas_rn):

  P=0
  N=0
  E=0
  for col in dt.columns:
    if 'AMES' in col:
      if '+' in str(dt[col].iloc[0]):
        P+=1
      elif '-' in str(dt[col].iloc[0]):
        N+=1
      elif 'E' in str(dt[col].iloc[0]):
        E+=1
  pne=(f" P\n/E= {P}/{N}/{E}")


  P=0
  N=0
  E=0
  for col in dt.columns:
    if 'in vitro' in col:
      if '+' in str(dt[col].iloc[0]):
        P+=1
      elif '-' in str(dt[col].iloc[0]):
        N+=1
      elif 'E' in str(dt[col].iloc[0]):
        E+=1

  vit_overall= (f" P\n/E = {P}/{N}/{E}")

  P=0
  N=0
  E=0

  for col in dt.columns:
    if 'in vivo' in col:
      if '+' in str(dt[col].iloc[0]):
        P+=1
      elif '-' in str(dt[col].iloc[0]):
        N+=1
      elif 'E' in str(dt[col].iloc[0]):
        E+=1



  viv_overall=(f" P\n/E = {P}/{N}/{E}")

  summary_df=pd.DataFrame({ 'Ames_Overall' :(str(dt['AMES Overall'].iloc[0])+ ' '+ str(pne)), 'vitro_overall':vit_overall , 'vivo_overall':viv_overall , 'CARC_overall':dt['Rodent Carcinogenicity Overall'].iloc[0] ,'IARC':dt['IARC Classification'].iloc[0]}, index=[cas_rn])
  return summary_df

# Function to extract all references
def extract_references(text):
    # Split by '#', ignore the first part (non-reference content)
    parts = text.split('#')[1:]
    # For each part, stop at the first ';' if it exists
    references = [part.split(';')[0].strip() for part in parts]
    return references


def ECVAM_neg_overall(cas_rn):
  import pandas as pd

  df_dict = {
      'df_ames': None,
      'df_mcgm': None,
      'df_mnvit': None,
      'df_cavit': None,
      'df_mnvivo': None,
      'df_cavivo': None,
      'df_tgr': None,
      'df_uds': None,
      'df_comet': None,
      'df_carc': None
  }

  # read ECVAM neg xlsx data
  df=pd.read_excel(ECVAM_NEG_FILE,header=0, skiprows=[0])
  df.dropna(axis='columns',how='all')
  for col in df.columns:
    if 'Unnamed' in col:
      df.drop(columns=col,inplace=True)
  df.rename(columns={'CAS No.' : 'CAS_no'}, inplace=True)

  #display different subtables with info in it
  pd.set_option('display.max_colwidth', None)
  pd.options.mode.chained_assignment = None  # default='warn'

  #dt=df.query(f'CAS_no == "{cas_rn}"')
  dt = df[df['CAS_no'] == cas_rn]

  if dt.empty:
    print(f"ECVAM negatives: No data found for {cas_rn}")
    return None, None, None, None, None, None, None, None, None, None, None, None, None
  else:
    print(f"ECVAM negatives: Data found for {cas_rn}")
    list_subtables = ['AMES', 'MCGM', 'MNvit', 'CAvit', 'MNvivo', 'CAvivo', 'TGR', 'UDS', 'COMET', 'CARC']

    for keyword, variable_name in zip(list_subtables, df_dict.keys()):
        result = ECVAM_neg_subtable(dt, keyword)  # Call the function
        if result is not None:
            df_dict[variable_name] = result  # Update the dictionary
        else:
            df_dict[variable_name] = None  # Set to None in the dictionary


    add_info=pd.DataFrame()
    add_info['other studies']=dt[['Other Tests & Notes']].copy()
    if add_info.empty:
      add_info=None





    summary=ECVAM_neg_summary_table(dt,cas_rn)

    # Access the DataFrames from the dictionary
    df_list = [df_dict['df_ames'], df_dict['df_mcgm'], df_dict['df_mnvit'], df_dict['df_cavit'],
              df_dict['df_mnvivo'], df_dict['df_cavivo'], df_dict['df_tgr'], df_dict['df_uds'],
              df_dict['df_comet'], df_dict['df_carc']]

    df_ref={}
    df_ref_list=[]
    for df in df_list:
      if df is not None:
        for col in df.columns:
          if ('Literature' in col) or ('reference' in col) or ('other' in col):
            df_ref_list.append( df[col].apply(extract_references))


    #create references dataframe
    processed_data = []

    for series in df_ref_list:
        # Extract references and essay name
        references = series.iloc[0]  # First element of the series (list of references)
        essay_name = series.name.split()[0]  # First word of the series name
        unique_references = list(set(references))  # Remove duplicates
        processed_data.append({"essay": essay_name, "references": unique_references})

    # Create a formatted DataFrame
    formatted_data = []
    for item in processed_data:
        essay = item["essay"]
        references = item["references"]
        for idx, ref in enumerate(references):
            formatted_data.append({"essay": essay, "unique_references": ref})

    # Create the final DataFrame
    final_df = pd.DataFrame(formatted_data)

    # Remove duplicates within each group
    final_df = final_df.groupby('essay', group_keys=False).apply(
        lambda group: group.drop_duplicates(subset=["unique_references"])
    )

    # Mask repeated essay names
    final_df["essay"] = final_df["essay"].mask(final_df["essay"].duplicated(), "")

    # Reset index for a clean display
    final_df = final_df.reset_index(drop=True)


    for df in df_dict.keys():
      if df_dict[df] is not None:
        df_dict[df]=df_dict[df]

    return summary,df_dict['df_ames'], df_dict['df_mcgm'], df_dict['df_mnvit'], df_dict['df_cavit'],df_dict['df_mnvivo'], df_dict['df_cavivo'], df_dict['df_tgr'], df_dict['df_uds'],df_dict['df_comet'], df_dict['df_carc'],add_info,final_df



# --- ECVAM POSITIVE FUNCTIONS --- #

def subtable_ECVAM(dt,desinenza,new_desinenza,overall):
  import numpy as np
  col_list=[]
  for col in dt.columns:
    if str(desinenza) in col or col==str(overall):
      col_list.append(col)
  new_df=dt[col_list].copy()
  new_df.dropna(axis='columns',how='all',inplace=True)
  # print(new_df.empty)
  if not new_df.empty:
    for col in new_df.columns:
      new_df.rename(columns={col:col.replace(str(desinenza),str(new_desinenza))},inplace=True)

    return new_df
  else:
    return None

def startcleanECVAM_pos_references():
  df_ref= pd.read_excel(ECVAM_POS_FILE, sheet_name="Database References List")
  df_ref.dropna(axis='columns',how='all', inplace=True)
  df_ref.dropna(how='all', inplace=True)
  pd.set_option("display.max_columns", None)

  for index in df_ref.index:
    if not str(df_ref.loc[index,'List of References']).startswith('['):
      df_ref.drop(index, inplace=True)

  df_ref['List of References']=df_ref['List of References'].astype(str)
  df_ref['Unnamed: 1']=df_ref['Unnamed: 1'].astype(str)
  df_ref['Concatenated'] = df_ref['List of References'].str.cat(df_ref['Unnamed: 1'], sep=' ')
  df_ref.drop(columns=['List of References', 'Unnamed: 1'], inplace=True)
  df_ref.rename(columns={'Concatenated': 'List of References'}, inplace=True)

  # Split into two columns
  df_ref[['Numerical Value', 'Reference Text']] = df_ref['List of References'].str.extract(r'\[(\d+)\]\s*(.+)')

  return df_ref

def ECVAM_pos_overall(cas_rn,details):
  import pandas as pd
  import re
  import numpy as np

  pd.set_option('display.max_columns', None)
  pd.set_option('display.max_rows', None)
  pd.set_option('display.max_colwidth', None)


  summary_df,ames_df, vit_MLA, vit_MN, vit_CA, viv_MN, viv_CA, viv_UDS, vivo_TGR, vivo_DNA, CARC, add_info, lit_table = None, None, None, None, None, None, None, None, None, None, None, None, None


  # read DeepAmes xlsx data
  df=pd.read_excel(ECVAM_POS_FILE, header=0, skiprows=[0])
  df.dropna(axis='columns',how='all')

  # Allow to overwrite dt value
  pd.options.mode.copy_on_write = True

  # Create a dictionary to store new column names
  new_column_names = {}
  index=0
  # Loop through columns
  for column in df.columns:
      # Check if the value in the first row is not NaN
      if pd.notna(df.at[0, column]) and index<3:
          # Create the new column name:
          new_name = 'CSCL-ISHL_' + str(df.at[0, column]).strip().replace('  ', '_')
          new_column_names[column] = new_name
          index+=1
      elif pd.notna(df.at[0, column]) and (index<6 and index>=3):
          new_name = 'CSCL-ISHL_' + str(df.at[0, column]).strip().replace('  ', '_')+str('.3')
          new_column_names[column] = new_name
          index+=1
      elif pd.notna(df.at[0, column]) and index>=6:
          new_name = 'CSCL-ISHL_' + str(df.at[0, column]).strip().replace('  ', '_')+str('.7')
          new_column_names[column] = new_name
          index+=1

  # Rename columns in one step
  df = df.rename(columns=new_column_names)

  df.dropna(axis='columns',how='all')
  df.drop(columns=['Chem\nAgora\nLink', 'Che\nLIST','Unnamed: 21','Unnamed: 62', 'Unnamed: 116', 'Unnamed: 131' ],inplace=True)
  df.drop(0,inplace=True)
  df.rename(columns={'+':'vitro_overall_+' , '-' : 'vitro_overall_-', '+.1': 'vivo_overall_+', '-.1': 'vivo_overall_-', 'CAS No. cleaned' : 'CAS_no_cleaned'  }, inplace=True)
  pd.set_option("display.max_columns", None)
  df.rename(columns={'CAS No. cleaned' : 'CAS_no_cleaned'}, inplace=True)

  #call query function
  # dt=df.query(f'CAS_no_cleaned == "{cas_rn}"')
  dt = df[df['CAS_no_cleaned'] == cas_rn]

  if not dt.empty:
    print(f"ECVAM positives: Data found for {cas_rn}")
    vitro_overall=(f" P\n= {int(dt['vitro_overall_+'].iloc[0])} / {int(dt['vitro_overall_-'].iloc[0])} ")
    vivo_overall=(f" P\n= {int(dt['vivo_overall_+'].iloc[0])} / {int(dt['vivo_overall_-'].iloc[0])} ")

    list_ames=['CSCL-ISHL_(-S9)', 'CSCL-ISHL_(+S9)', 'CSCL-ISHL_Overall', ' Kirkland et al 2005 & 2011 [1, 2]*', 'US NTP', 'EFSA','SCCS', 'CosE', 'BASF', 'GSK', 'ECHA',	'ISSTox']
    positive=0
    negative=0
    equivocal=0
    for col in list_ames:
        if '+' in str(dt[col].iloc[0]):
          positive+=1
        elif '-' in str(dt[col].iloc[0]):
          negative+=1
        elif 'E' in str(dt[col].iloc[0]):
          equivocal+=1
    pne=(f" P\n/E= {positive} / {negative} / {equivocal} ")
    pd.options.mode.copy_on_write = True
    a=str(f" {dt['Ames Overall '].iloc[0]}  {str(pne)}")
    summary_df=pd.DataFrame([{ 'Ames_Overall' :a, 'vitro_overall':vitro_overall , 'vivo_overall':vivo_overall , 'CARC_overall':dt['CARC Overall '].iloc[0] }], index=[cas_rn])
    summary_df=summary_df

    if details=='on':

      ames_df= dt[['CSCL-ISHL_(-S9)', 'CSCL-ISHL_(+S9)', 'CSCL-ISHL_Overall', ' Kirkland et al 2005 & 2011 [1, 2]*', 'US NTP', 'EFSA','SCCS', 'CosE', 'BASF', 'GSK', 'ECHA',	'ISSTox',	'Literature & Notes',	'Ames Overall ']].copy()
      print('AMES TABLE')
      print(ames_df)
      ames_df.dropna(axis='columns',how='all',inplace=True)
      if not ames_df.empty:
        ames_df=ames_df
        print(ames_df)
      else:
        ames_df=None

      # print('VITRO MLA TABLE')
      vit_MLA=subtable_ECVAM(dt,'.1','_vit_MLA','in vitro MLA Overall ')
      # print('VITRO MICRONUCLEOUS TABLE')
      vit_MN=subtable_ECVAM(dt,'.2','_vit_MN','in vitro MN Overall ')
      # print('VITRO CROMOSOMIAL ABERRATIONS TABLE')
      vit_CA=subtable_ECVAM(dt,'.3','_vit_CA','in vitro CA Overall ')
      # print('VIVO MICRONUCLOUS TABLE')
      viv_MN=subtable_ECVAM(dt,'.4','_viv_MN','in vivo MN Overall ')
      # print('VIVO CROMOSOMIAL ABERRATIONS TABLE')
      viv_CA=subtable_ECVAM(dt,'.5','_viv_CA','in vivo CA Overall')
      # print('VIVO UNSCHEDULED DNA SYNTHESIS TABLE')
      viv_UDS=subtable_ECVAM(dt,'.6','_viv_UDS','in vivo UDS Overall')


      # print('TRANSGENIC RODENT TABLE')
      vivo_TGR=dt[[' Kirkland et al 2005 & 2011 [1, 2]*.7', 'EFSA.7','SCCS.7', 'ECHA.7',	'ISSTox.7',	'Literature & Notes.7',	'transgenic Overall']].copy()
      for col in vivo_TGR.columns:
        vivo_TGR.rename(columns={col:col.replace('.7','_viv_TGR')},inplace=True)
      vivo_TGR.dropna(axis='columns',how='all',inplace=True)
      vivo_TGR.dropna(how='all',inplace=True)
      if not vivo_TGR.empty:
        vivo_TGR=vivo_TGR

      # print('VIVO DNA DAMAGE TABLE')
      vivo_DNA_d=dt[[' Kirkland et al 2005 & 2011 [1, 2]*.8', 'EFSA.8','SCCS.8', 'CosE.7', 'GSK.7', 'ECHA.8',	'Literature & Notes.8',	'in vivo DNA damage Overall']].copy()
      for col in vivo_DNA_d.columns:
        vivo_DNA_d.rename(columns={col:col.replace('.7','_viv_DNA_d')},inplace=True)
        vivo_DNA_d.rename(columns={col:col.replace('.8','_viv_DNA_d')},inplace=True)
      vivo_DNA_d.dropna(axis='columns',how='all',inplace=True)
      if not vivo_DNA_d.empty:
        vivo_DNA=vivo_DNA_d


      # print('CARCINOGENICITY TABLE')
      CARC=dt[['CSCL-ISHL_IARC.7','CSCL-ISHL_CPDB.7','CSCL-ISHL_[other].7',' Kirkland et al 2005 & 2011 [1, 2]*.9', 'NTP', 'EFSA.9','SCCS.9', 'CosE.8', 'BASF.7', 'GSK.8', 'ECHA.9',	'ISSTox.8',	'Literature & Notes.9',	'CARC Overall ']].copy()
      for col in CARC.columns:
        CARC.rename(columns={col:col.replace('.7','_CARC')},inplace=True)
        CARC.rename(columns={col:col.replace('.8','_CARC')},inplace=True)
        CARC.rename(columns={col:col.replace('.9','_CARC')},inplace=True)
      CARC.dropna(axis='columns',how='all',inplace=True)
      if not CARC.empty:
        CARC=CARC

      add_info=pd.DataFrame()
      # print('OTHER STUDIES')
      add_info['other studies']=dt[[' (a)']].copy()
      add_info.dropna(axis='columns',how='all',inplace=True)
      add_info.dropna(how='all',inplace=True)
      if not add_info.empty:
        add_info=add_info

      df_ref=startcleanECVAM_pos_references()
      lit_array=[]
      # Iterate over each column in the DataFrame
      for col in dt.columns:
          if str(col).startswith('Literature'):  # Check for the specific column
            for ind in dt.index:
              col_value = str(dt.loc[ind, col])  # Ensure it's a string

              values_within_brackets = []
              # Find all ranges or individual numbers within brackets
              # Regex to match ranges, individual numbers, and lists within brackets
              matches = re.findall(r'[+-]?\[(\d+(?:-\d+)?(?:,\s*\d+)*)\]', col_value)
              for match in matches:
                # Split the match by commas to handle multiple numbers or ranges
                parts = match.split(',')
                for part in parts:
                  part = part.strip()  # Remove extra spaces
                  if '-' in part:  # It's a range
                    start, end = map(int, part.split('-'))
                    values_within_brackets.extend(range(start, end + 1))
                  else:  # It's a single number
                    values_within_brackets.append(int(part))

              values_as_integers = [int(value) for value in values_within_brackets]
              #print(f"Row {ind}: {values_as_integers}")
              for index in df_ref.index:
                lit=None
                if int(df_ref.loc[index,'Numerical Value']) in values_as_integers:
                  lit=df_ref.loc[index,'List of References']
                  if lit not in lit_array:
                    lit_array.append(lit)
      lit_table={}
      if lit_array:

        lit_table=pd.DataFrame(data=list(lit_array), columns=['List of References'])
        lit_table=lit_table.dropna(axis='columns',how='all',inplace=True)
        if (not lit_table.empty) or (lit_table is not None):
          lit_table=lit_table
        else:
          lit_table=None


      return summary_df,ames_df,vit_MLA,vit_MN,vit_CA,viv_MN,viv_CA,viv_UDS,vivo_TGR,vivo_DNA,CARC,add_info,lit_table
    else:
      return summary_df,None,None,None,None,None,None,None,None,None,None,None,None




  else:
    print(f" No data found for cas_rn={cas_rn}")
    return None,None,None,None,None,None,None,None,None,None,None,None,None


# --- CAS VALIDATE ----

def cas_validation(cas):
	import sys, re
	"""Validates if a provided CAS number could exist"""

	try:
		cas_match = re.search(r'(\d+)-(\d\d)-(\d)',cas) # Takes into account the standard CAS formatting e.g. 7732-18-5
		cas_string = cas_match.group(1) + cas_match.group(2) + cas_match.group(3)

		increment = 0
		sum_cas = 0

		# Slices the reversed number string
		for number in reversed(cas_string):
			if increment == 0:
				validate = int(number)
				increment = increment + 1
			else:
				sum_cas = sum_cas + (int(number) * increment)
				increment = increment + 1

		# Does the math
		if validate == sum_cas % 10:
			print('True') # Can be removed if not used on Terminal
			return True
		else: 
			print('False') # Can be removed if not used on Terminal
			return False
	except:
		print('False') # Choose the action for errors you like
		return False



# --- CAS TO INCHI-KEY ---
def generate_url(cas_number):
    """Generates the URL for the NCI Cactus API."""
    base_url = "https://cactus.nci.nih.gov/chemical/structure/{}/stdinchikey"
    return base_url.format(cas_number)

def fetch_url_content(cas_number):
    """Fetches content from the specified URL."""
    url = generate_url(cas_number)
    try:
        response = requests.get(url, timeout=12)  # Add a timeout to prevent indefinite hanging
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error retrieving data for CAS {cas_number}: {e}"  # More informative error message



# --- Django View ---
def progress_view(request):
    if 'progress' in request.session:
        return JsonResponse(request.session['progress'])
    else:
        return JsonResponse({'message': 'No progress information available'})

# --- Django View ---
def progress_view(request):
    if 'progress' in request.session:
        return JsonResponse(request.session['progress'])
    else:
        return JsonResponse({'message': 'No progress information available'})

class QueryAPIView(APIView):
 def post(self, request, format=None):
        # get data from the user frontend interface
        cas_rn = request.data.get('cas_rn')
        details = bool(request.data.get('details'))
     
        if not cas_rn or not cas_validation(cas_rn):
            return Response({"error": "CAS number inválido."}, status=status.HTTP_400_BAD_REQUEST)

       
        inchi_key = str(fetch_url_content(cas_rn)).replace('InChIKey=', '')
        inchi_key_fetched = True
        results = {}

        if cas_rn:
            results.update({
                'DeepAmes': query_deepames(cas_rn),
                'Hansen': query_hansen(cas_rn),
                'OECD_vivo': query_oecd_vivo(cas_rn),
                'OECD_Chromosome_vitro': query_oecd_chromosome(cas_rn),
                'IARC': query_iarc(cas_rn),
                'PPRTV&IRIS': query_IRIS_PPRTV(cas_rn),
                'HOMNA': query_homna(cas_rn),
            })

        amescebs_summary, amescebs_supersummary = query_amescebs(cas_rn, details)
        results['AMESCEBS_supersummary'] = amescebs_supersummary
        results['AMESCEBS_summary'] = amescebs_summary

        opf_genotox_summary, opf_genotox_ref, opf_refpoint_ref, opf_refvalue_ref = query_openfoodtox(cas_rn)
        results['OpenFoodTox_genotox_summary'] = opf_genotox_summary
        results['OpenFoodTox_genotox_ref'] = opf_genotox_ref
        results['OpenFoodTox_refpoint_ref'] = opf_refpoint_ref
        results['OpenFoodTox_refvalue_ref'] = opf_refvalue_ref

        ecvam_neg_results = query_ecvam_neg(cas_rn)
        if ecvam_neg_results:
            results.update(ecvam_neg_results)

        ecvam_pos_results = query_ecvam_pos(cas_rn, details)
        if ecvam_pos_results:
            results.update(ecvam_pos_results)

        if inchi_key:
            ccris_dg, ccris_summary = query_ccris(inchi_key, details)
            if details == 'on' and ccris_dg is not None:
                for i, df in enumerate(ccris_dg):
                    if df is not None:
                        df = add_cas_db_version_identificative(df, cas_rn, CCRIS_FILE)
                        df = df.transpose()
                        ccris_dg[i] = df  
            if ccris_summary is not None:
                ccris_summary = add_cas_db_version_identificative(ccris_summary, cas_rn, CCRIS_FILE)
                ccris_summary = ccris_summary.transpose()

            results['CCRIS_Summary'] = ccris_summary
            results['CCRIS_Data'] = ccris_dg


        all_empty = all(result is None or 
                        (isinstance(result, tuple) and all(r is None or (hasattr(r, 'empty') and r.empty) for r in result)) or 
                        (hasattr(result, 'empty') and result.empty)
                        for result in results.values())
        if all_empty:
            return Response({"error": "No se encontraron datos para el identificador proporcionado."}, status=status.HTTP_404_NOT_FOUND)

      
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, result in results.items():
                if result is not None:
                   
                    if sheet_name == 'CCRIS_Summary' and hasattr(result, 'to_excel'):
                        for col in result.select_dtypes(include=['object']).columns:
                            try:
                                result[col] = result[col].astype(str)
                            except Exception as e:
                                result[col] = result[col].fillna("N/A")
                        result.to_excel(writer, sheet_name='CCRIS_Summary', index=True)
                    elif sheet_name == 'CCRIS_Data' and details == 'on':
                        dg_list = result
                        if dg_list is not None:
                            for index, dg in enumerate(dg_list):
                                if not dg.empty:
                                    for col in dg.select_dtypes(include=['object']).columns:
                                        try:
                                            dg[col] = dg[col].astype(str)
                                        except Exception as e:
                                            dg[col] = dg[col].fillna("N/A")
                                    dg.to_excel(writer, sheet_name=f'CCRIS_Details_{index}', index=True)
                    elif hasattr(result, 'to_excel'):
                        for col in result.select_dtypes(include=['object']).columns:
                            try:
                                result[col] = result[col].astype(str)
                            except Exception as e:
                                result[col] = result[col].fillna("N/A")
                        result.to_excel(writer, sheet_name=sheet_name, index=True)
                   
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{cas_rn}_results.xlsx"'
        return response