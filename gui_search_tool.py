# Import Packages

import streamlit as st
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains as Actions
import os
from tabula import read_pdf
import regex as re


# Function Extract Page

def ExtractGooglePage(driver):

    "extracts google page and converts it to a table"

    # Results Collect

    resultLinks=driver.find_elements(By.XPATH,"//a[@href and @ping]")

    contents=driver.find_elements(By.XPATH,"//div[@lang='en']")

    contentsMatch=["\n".join(x.text.split("\n")[:-1]) for x in contents]

    contentsMatchMethod2=["\n".join(x.text.split("\n")[:-2]) for x in contents]

    extractedInfo=[]

    for result in resultLinks:

        indexContent=None

        # Finding Index Via Multiple Methods

        try:

            indexContent=contentsMatch.index(result.text)
        
        except ValueError:

            try:

                indexContent=contentsMatchMethod2.index(result.text)
            
            except ValueError:

                pass
        
        # Assigning Object

        if indexContent is not None:

            url=result.get_attribute("href")

            # Saving PDF Files

            if url[-4:]==".pdf":

                try:

                    downloadPDF=WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH,"//a[@href='%s']"%url))
                                )   

                    downloadPDF.click()

                except Exception:

                    pass 

            title=contents[indexContent].text.split("\n")[0]

            text=contents[indexContent].text.split("\n")[-1]

            print("Link:",result.text)

            print("Content Match:",contentsMatch[indexContent])

            if title!="":

                extractedInfo.append({"URL":url,"Title":title,"Text":text})   


    return pd.DataFrame.from_dict(extractedInfo,orient='columns') 


def SearchGoogle(keyWords):

    "searches google for keywords, navigates page by page and extract its content."

    # Search Token

    tokenID=str(pd.Timestamp.now()).replace("-","").replace(" ","").replace(":","").replace(".","")

    # Configurations

    pdfDirectory=os.getcwd()+"\\Pdf Files\\%s"%tokenID

    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', {
    "download.default_directory": pdfDirectory, #Change default directory for downloads
    "download.prompt_for_download": False, #To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
    })    

    #options.add_argument("--headless")

    # Hit Google For Search Results

    driver = webdriver.Chrome(service=Service("chromedriver.exe"),options=options)

    # Home Page

    webPage=driver.get('https://www.google.com/')

    # Maximizing The Window

    driver.maximize_window()

    # Find the search bar and enter the keywords followed by enter click

    googleSearchBar=WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,"textarea[type='search']"))
                )
    
    googleSearchBar.send_keys(keyWords)

    googleSearchBar.send_keys(Keys.ENTER)

    maxPageNum=10

    numPagesExtracted=0

    allContent=[]

    # Extract The Content From Each Page

    while numPagesExtracted<maxPageNum:

        pageContentTable=ExtractGooglePage(driver)

        allContent.append(pageContentTable)

        numPagesExtracted+=1

        # Click Next Page If Num Of Pages Extracted is less than maximum pages

        if numPagesExtracted<maxPageNum:

            nextPageButton=WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.ID,"pnnext"))
                                        )

            
            nextPageButton.click()
    

    return pd.concat(allContent,ignore_index=True),tokenID


def PDFtoExcel(filePath):

    # File Name Identifier

    fileNameRX=re.compile(r"[^//]+.pdf")

    fileName=fileNameRX.search(filePath).group().replace(".pdf","")

    # Extract All Pages

    pages =read_pdf(filePath,pages="all")

    # Create Table Directory If Not Exists

    if not os.path.exists('Tables'):
        os.makedirs('Tables')

    # Write To Excel File

    with pd.ExcelWriter("Tables/%s.xlsx"%fileName) as writer:

        for pageNum,page in enumerate(pages):

            page.to_excel(writer, sheet_name=str(pageNum))  


    return {"Status":"Success"} 


# COnfigs

st.set_page_config(layout="wide")

st.title("Search Tool")


# Get Input From User

keyWords = st.text_input(label="Search",placeholder="Enter Any Text To Search In Google")

print("keywords:",keyWords)

# Extract Information From Google

if keyWords:

    content,tokenID=SearchGoogle(keyWords)

    # Display Results In Table

    st.write(content)

    st.download_button(label="Download Results",
                    data=content.to_csv(index=False).encode('utf-8'),
                    file_name='searchresults.csv',
                    mime='text/csv')

    st.write("PDF is available under the folder /Pdf Files/%s/"%tokenID)

    st.write("Converted tables in excel format will be inside folder /Tables/%s/"%tokenID)


st.write("Edit Search Bar For Changed Results")





        