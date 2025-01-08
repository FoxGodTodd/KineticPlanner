import pandas as pd
import random
import re
import numpy as np
import streamlit as st

# Function to process user input and select the sites
def select_sites(df,k,selected_sites, selected_ids,shots_dict):
    kshotcount = 0
    requested_count = int(shots_dict[k])
    environments = df['Environment'].unique()
    environment_count = {environment: 0 for environment in environments}  # To track counts per environment
    total_count = len(df['Media Format Name'].to_numpy())
    uniquetotal = len(df['Media Format Name'].unique())
    print(total_count)
    envpairs = []
    for env in environments:
        availableformats = df[df['Environment'] == env]['Media Format Name']
        uniqueformats = availableformats.unique()
        available_count = len(availableformats.to_numpy())
        print('Available and unique formats: ', available_count,len(uniqueformats))
        
        cnt = np.round((requested_count*((len(uniqueformats)/uniquetotal)/len(environments)))+0.2)
        print(f'Chosen Count for {env}: {cnt}')
        envpairs.append((env,cnt))

    # Iterate over each pair
    for key, count in envpairs:
        Mtypes = []
        env_type = key
        envrows = df[df['Environment'] == env_type]
        if env_type is 'nan':
            envrows = df
        if 'Postar ID' not in envrows.columns:
            envrows['Postar ID'] = range(len(envrows['Media Format Name'].to_numpy()))
        envrowsUnique = envrows.drop_duplicates(subset='Media Format Name')

        # Find the required number of sites for this format
        for index, row in envrowsUnique.iterrows():
            if row['Postar ID'] not in selected_ids and kshotcount <  requested_count:
                selected_sites.append(row)
                selected_ids.add(row['Postar ID'])
                environment_count[env_type] += 1  # Increment the count for this format
                kshotcount +=1

            if environment_count[env_type]  >= count:
                break
        
        for jindex, jrow in envrows.iterrows():
            if jrow['Postar ID'] not in selected_ids and kshotcount <  requested_count:
                selected_sites.append(jrow)
                selected_ids.add(jrow['Postar ID'])
                environment_count[env_type] += 1  # Increment the count for this format
                kshotcount +=1

            if environment_count[env_type]  >= count:
                break        
                

        # If we don't have enough sites, notify the user
        if environment_count[env_type]  < count:
            print(f"Warning: Could not find {count} sites for {k} in environment {env_type}")
            #st.write(f"I could not find {count} sites for {k} in environment {env_type}...'")

    # After processing all formats, inform the user about the results
    for env_type, found_count in environment_count.items():
        print(f"Found {found_count} sites for {k} in environment {env_type}")
        st.write(f"Found {found_count} sites for {k} in environment {env_type}")
    # Return the selected rows as a DataFrame
    return selected_sites,selected_ids

def reference_check(df_copy,bRef,selected_sites,selected_ids,shots_dict,lenchoice):
    df = df_copy[df_copy['Campaign Code']==bRef]
    if df.empty:
        print("No data found for the given postcode and booking reference.")
    elif len(selected_sites) < lenchoice:
        # Show user the available formats
        uniqueEnvirons = df['Environment'].unique()
        print(f"\nFor the {bRef} campaign, there is/are {len(uniqueEnvirons)} available Environment/s:")
        for key in uniqueEnvirons:
            liveformats = df[(df['Environment']==key)]['Media Format Name'].unique()
            print(f" > {key} with these formats {str(liveformats)}")

        # Select sites based on the user input
        selected_sites,selected_ids = select_sites(df,bRef,selected_sites,selected_ids,shots_dict)
    return(selected_sites,selected_ids)	

# Main function to run the whole process
def main(sitelist,choice):
	# Load the Excel file
    df_copy = sitelist.copy()
    
    # Input from the user
    postcode = choice[0]    
    date = choice[1]
    lenchoice = choice[2]
    
    references = df_copy['Campaign Code'].unique()

    print('\nIn this postcode, these are the available campaigns this day:\n',references)
    
    return(references,df_copy,lenchoice)

def make_dataframe(df,shots_dict,choices,arniesites):
    selected_sites = []
    selected_ids = arniesites
    
    references,dfcopy,lenchoice = main(df,choices)
    
    for Refs in references:
        selected_sites,selected_ids = reference_check(dfcopy,Refs,selected_sites,selected_ids,shots_dict,lenchoice)
        
    selected_Df = pd.DataFrame(selected_sites)

    if selected_Df.empty:
        print("No sites could be selected based on the given criteria.")
    else:
        if 'Panel' not in selected_Df.columns:
            selected_Df['Panel'] = '1'
        selected_Df.rename(columns={'Campaign':'Brand','Panel Name':'Address','Campaign Code':'Booking IDs', 
                           'Contractor Name':'Media Owner','Panel':'Panel Code', 'Size':'Format'},inplace=True)
        selected_Df['Map'] = ''
        selected_Df['Notes'] = ''
        selected_Df['File Name'] = ''
        selected_Df['Coordinates'] = ''
        frame_df = pd.read_excel("https://github.com/FoxGodTodd/KineticPlanner/raw/main/FrameIDLatLon.xlsx")
        if 'Postar ID' in selected_Df.columns:
            merged_df = pd.merge(selected_Df, frame_df, how='left', left_on='Postar ID', right_on='routeFrameID')
            merged_df['Coordinates'] = merged_df['latitude'].astype(str)+','+merged_df['longitude'].astype(str)
            selected_Df['Coordinates'] = merged_df['Coordinates'].to_list()
        elif 'Postcode' in selected_Df.columns:
            frame_df = frame_df.drop_duplicates(subset='Postcode')
            merged_df = pd.merge(selected_Df, frame_df, how='left', left_on='Postcode', right_on='postCode')
            merged_df['Coordinates'] = merged_df['latitude'].astype(str)+','+merged_df['longitude'].astype(str)
            selected_Df['Coordinates'] = merged_df['Coordinates'].to_list()
        
        # Export selected sites to a new Excel file
        selected_Df=selected_Df[['Map','Brand','Format','Address','Coordinates','Postcode','File Name','Notes','Site Number','Media Owner','Panel Code','Booking IDs']]
        #selected_Df.to_excel('SelectedSites.xlsx', index=False)
        print(f"Selected sites have been saved to 'SelectedSites.xlsx'.")
    return(selected_Df)
