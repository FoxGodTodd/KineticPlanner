#Kinetic Interface 

import streamlit as st
from datetime import datetime
import pandas as pd
import Kinetake2
import time
import random
import re
import numpy as np

# Main Streamlit app
def app():
    # Title for the app
    chosen = False
    st.title('Kinetic Brief Planner')
    
    st.header("For each area and date, only certain campaigns, formats and environments will be available")
    st.write("The chosen number of shots will be divided evenly across available environments")
    
    df = st.file_uploader("Upload the kinetic site list")
    
    filenames = []
    if df: 
        uploadedFilename = df.name
        # Regex to match "K" followed by 4 or more digits
        match = re.search(r'K\d{4,}', uploadedFilename)
        if(match is not None):
            filenames.append(str(match.group()))

    # Step 1: User selects the type of brief
    brief_type = st.radio(
        "Please select the type of brief:",
        ('New Kinetic only brief','Add to existing brief')
    )

    # Step 2: Define the variables that will be passed to the function
    is_arn_brief = brief_type == 'Add to existing brief'
    postcode = None
    df2 = None
    campaigns = None
    
    # Step 5: Once the postcode is selected or entered, call the Find options function
    total_sites = st.number_input("Enter the number of maximum added sites (less than 20)", min_value=0, max_value=20, value=0, step=1)
    
    # Date input (with the year defaulting to 2024)
    today = datetime.today()
    date_input = st.date_input(
        "Select a date (default year is 2024)", 
        min_value=datetime(2024, 1, 1), 
        max_value=datetime(2030, 12, 31), 
        value="today",
        format = "DD/MM/YYYY"
    )
    
    # Step 3: Handle ARN brief (option 1)
    if is_arn_brief and chosen is False:
        # Request the user to upload a CSV
        uploaded_file = st.file_uploader("Upload your previous brief")
        
        if uploaded_file is not None:
            # Read the excel into a DataFrame
            with st.spinner('Loading...'):
                df2 = pd.read_csv(uploaded_file)
		
            # Check if the 'Postcode' column exists
            if 'Postcode' in df2.columns:
                df2 = df2.dropna(subset='Postcode')
                # Get the postcode from the last row of the 'Postcode' column
                postcode = df2['Postcode'].iloc[-1]
                st.write(f"Based on the location of JCD sites in this brief, the Kinetic sites will be searched in the vicinity of {postcode}")
            else:
                st.write("File does not contain any post code information we can use")
                postcode = st.text_input("Enter the search postcode manually:")

    # Step 4: Handle Kinetic only brief (option 2)
    else:
        # Ask for the postcode input from the user
        postcode_option = st.radio("How would you like to select a postcode?", ("Enter postcode manually", "Pick for me"))
        if postcode_option == "Enter postcode manually":
            postcode = st.text_input("Enter the postcode:")
        else:
            # If "Pick for me" is selected, show the multi-select for campaigns
            dftemp = pd.read_excel(df)
            if 'Campaign' not in dftemp:
                dftemp['Campaign'] = str(uploadedFilename).strip('.xlsx')
            CUnique = dftemp['Campaign'].unique()
            Clist = np.concatenate((['Include All Campaigns'],CUnique))
            campaigns = st.multiselect(
            "Select campaigns", 
            Clist,
            )
    
        if campaigns:
            # Filter the dataframe to include only the selected campaigns
            if(('Include All Campaigns') not in campaigns):
                filtered_df = dftemp[dftemp['Campaign'].isin(campaigns)]
            else:
                print('All included')
                filtered_df = dftemp
            
            input_date = date_input.strftime('%Y-%m-%d')
            filtered_df['Start'] = pd.to_datetime(filtered_df['Start'],errors='ignore')
            filtered_df['Finish'] = pd.to_datetime(filtered_df['Finish'],errors='ignore')
            filtered_df = filtered_df[(filtered_df['Start'] <= input_date)&(filtered_df['Finish'] >= input_date)]
            filtered_df['Postcode Slice'] = filtered_df['Postcode'].str.split(' ').str[0]
        
            # Count how many times each postcode appears in the selected campaigns
            postcode_campaign_count = filtered_df.groupby(['Postcode Slice'])['Campaign'].count()
            postcode_format_count = filtered_df.groupby(['Postcode Slice'])['Media Format Name'].count()
            print(postcode_campaign_count,postcode_format_count)
        
            # Get the top 5 postcodes with the most campaign occurrences
            top_postcodes_campaigns = postcode_campaign_count.nlargest(10)
            top_postcodes_formats = postcode_format_count.nlargest(10)
            print(top_postcodes_campaigns,top_postcodes_formats)
        
            # Randomly pick one of the top 10 postcodes
            if len(top_postcodes_campaigns) >= 1:
                campaignindex = top_postcodes_campaigns.index.tolist()
                formatsindex = top_postcodes_formats.index.tolist()
                shared = list(set(formatsindex) & set(campaignindex))
                if len(shared) > 0:
                    print(shared)
                    selected_postcode = shared[0]
                else:
                    selected_postcode = campaignindex[0]
                Pindex = filtered_df[filtered_df['Postcode Slice'] == selected_postcode].index.tolist()
                selected_postcode = filtered_df.at[Pindex[0],'Postcode']
            else:
                selected_postcode = dftemp['Postcode'].tolist()[0]
            st.write(f'Chosen postcode is {selected_postcode}')
            postcode = str(selected_postcode)

    if postcode and total_sites != 0:
        Chosen = True
        Find_options(postcode,df, total_sites, date_input,df2,filenames)

def Find_options(postcode,df,total_sites, date_input,df2,filenames):
    #formatlist = ['6 Sheet','6 Sheet illuminated', '6 Sheet Scrollers','Digital 6 Sheet', 'Digital 6s',
    #        'Digital 48 sheet','High Definition 48','','NaN','Digital 12 Sheet',None,'nan']
    input_date = date_input.strftime('%Y-%m-%d')
    st.write("Now pick the shots to plan for each live campaign in this area")
    arnieslist = set()
    
    references = ['No live campaigns for these options']
    choices = [postcode,input_date,int(total_sites)]
    
    df = pd.read_excel(df)
    dforiginal = df.copy()
    
    if 'Campaign' not in df:
        df['Campaign'] = str(filenames[0]).strip('.xlsx')
        
    if 'Campaign Code' not in df.columns:
        df['Campaign Code'] = str(filenames[0])
        
    if 'Media Format Name' not in df.columns:
        if 'Size' in df.columns:
            df['Media Format Name'] = df['Size']
        else:
            df['Media Format Name'] = 'Unknown'
    
    df = df.dropna(subset=['Postcode'])
    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])
    df = df[(df['Start'] <= input_date)&(df['Finish'] >= input_date)]
    df = df[(df['Postcode'].str.startswith(postcode[:postcode.find(' ')]+' ',na=False))]  

    references = df['Campaign Code'].unique()
    
    if len(references) < 1:
        st.write('I could not find any campaigns this day, please choose a different date')
    else:
        st.write('In this postcode, these are the available campaigns this day:'+str(references))
    shots_dict = {}
    
    if 'Environment' not in df.columns:
        df['Environment'] = "Roadside"
       
    for k in references:
        dfFiltered = df[df['Campaign Code']==k]
        uniqueEnvirons = dfFiltered['Environment'].unique()
        st.write(f"For the {k} campaign ({dfFiltered['Campaign'].to_numpy()[0]}), there is/are {len(uniqueEnvirons)} Environment/s available:")
        for key in uniqueEnvirons:
            liveformats = dfFiltered[(dfFiltered['Environment']==key)]['Media Format Name']
            st.write(f" > {key} with these formats; {str(list(liveformats.unique())).strip('[]')} in these amounts: {str(list(liveformats.value_counts())).strip('[]')}")
        shots_dict[k] = st.number_input(f"Combined number of Shots for {k}, ({dfFiltered['Campaign'].to_numpy()[0]})", min_value=0, value=1, step=1)
    
    # Display the inputs when the user clicks "Submit"
    if st.button('Submit'):	
        st.header("Submission Summary:")
        st.write(f"Postcode: {postcode}")
        st.write(f"Date: {date_input.strftime('%d/%m/%Y')}")
        st.write(f"Maximum Sites: {total_sites}")
        st.write("Chosen number of shots for each K-number:")
        kandshot = []
        for k, shots in shots_dict.items():
            kandshot.append(f"{k}: {shots} shot/s")
        st.write(str(kandshot).strip("[]"))
        
        with st.spinner('Making brief...'):
            framelocs = pd.read_excel('FrameIDLatLon.xlsx')
            if(df2 is not None):
                df2 = df2.dropna(subset=['Coordinates'])
                for i in range(len(df2['Coordinates'])):
                     koords = df2.at[i,'Coordinates']
                     koords = koords.strip('()')
                     latofframe = str(koords[:koords.find(',')-2])
                     print('Lat of Frame: ',latofframe)
                     if len(list(latofframe)) > 2: 
                         framelocs = framelocs.dropna(subset=['latitude'])
                         framelist = framelocs.index[framelocs['latitude'].str.startswith(latofframe,na=False)].tolist()
                         if len(framelist) > 1:
                             arnieslist.add(framelocs.at[framelist[0],'routeFrameID'])
                    
            dataframe = Kinetake2.make_dataframe(df,shots_dict,choices,arnieslist) 
            if(df2 is not None):
                dataframe = pd.concat([df2,dataframe])
            print(dataframe)
        if not dataframe.empty: dataframe.set_index("Map",inplace=True)
        st.header('Final Brief')
        st.write(dataframe)

# Run the Streamlit app
if __name__ == "__main__":
    app()
