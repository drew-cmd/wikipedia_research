import aiohttp
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import sqlite3
import logging
import time
import logging
import aiosqlite
from openai import AsyncOpenAI
from flask import Flask, jsonify, request
from flask_cors import CORS
import ast
from dotenv import load_dotenv
import os

# Initialize SQLite database
DATABASE = 'wiki_data.db'

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLite database
def initialize_database():
    try:
        with sqlite3.connect(DATABASE) as db:
            cursor = db.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS wiki_data (wikilink TEXT PRIMARY KEY, page_name TEXT, content TEXT, relevance_ranked TEXT)')
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")

# Check if the data exists in the database
def check_database(page_name, check):
    try:
        with sqlite3.connect(DATABASE) as db:
            cursor = db.cursor()
            cursor.execute(f'SELECT {check} FROM wiki_data WHERE page_name = ?', (page_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        logger.error(f"Error checking database: {e}")
        return None

async def save_to_database_async(wikilink, page_name, content, relevance_ranked):
    try:
        logger.info(f"Saving data to database: {wikilink}, {page_name}")
        async with aiosqlite.connect(DATABASE) as db:
            # Check if the row already exists in the database
            cursor = await db.execute('SELECT * FROM wiki_data WHERE page_name = ?', (page_name,))
            existing_row = await cursor.fetchone()
            
            if existing_row:
                # Row already exists, update the relevance_ranked column
                await db.execute('UPDATE wiki_data SET relevance_ranked = ? WHERE page_name = ?', (relevance_ranked, page_name))
            else:
                # Row doesn't exist, insert a new row
                await db.execute('INSERT INTO wiki_data (wikilink, page_name, content, relevance_ranked) VALUES (?, ?, ?, ?)',
                                 (wikilink, page_name, content, relevance_ranked))
            
            await db.commit()  # Commit changes to the database
        logger.info("Data saved successfully")
    except sqlite3.Error as e:
        logger.error(f"Error saving to database: {e}")



async def webScrapingAPI(wikilink, internal_wikis):

    # Load environment variables from .env file
    load_dotenv()

    # Access the API key
    api_key = os.getenv('OPENAI_API_KEY')

    client = AsyncOpenAI(api_key = api_key)

    internal_wikis = ", ".join(internal_wikis)

    try:
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=0.8,
            max_tokens=3000,
            messages=[
                {"role": "user",
                "content": "Original: " + wikilink + ". Can you rank the following list of internal wiki links in order from greatest to least relevance (and assign points from 1 - 10, 10 being the most) to the Original wikilink. Please output the result in a list called relevance_ranked. Ex: relevance_ranked = [\n (\"/wiki/Normandy\", 10),\n (\"/wiki/Normandy_(administrative_region)\", 9),\n (\"/wiki/France\", 8), (\"/wiki/Duchy_of_Normandy\", 7),\n (\"/wiki/Norman_language\", 6),\n (\"/wiki/Rouen\", 5),\n (\"/wiki/Caen\", 4),\n (\"/wiki/Flag_of_Normandy\", 3),\n (\"/wiki/Coat_of_arms_of_Normandy\", 2),\n (\"/wiki/Geographic_coordinate_system\", 1)]. Internal Wikis: " + "{internal_wikis}"
                }

            ]
        )

        #print(completion.choices[0].message)

        # Check if the response was successful
        if completion.choices:
            completion_message = completion.choices[0].message

            #print(completion_message.content)

            # Extract the relevance_ranked list content
            start_index = completion_message.content.find('[')
            end_index = completion_message.content.rfind(']')
            if start_index != -1 and end_index != -1:
                relevance_ranked_str = completion_message.content[start_index:end_index+1]
                #print("Extracted relevance_ranked_str: ", relevance_ranked_str)
         
                # Safely evaluate the string as a Python list
                try:
                    relevance_ranked = ast.literal_eval(relevance_ranked_str)
                    #print("relevance_ranked: ", relevance_ranked)

                    # Create HTML code for each link and relevance score
                    links_html = ''
                    for link, relevance_score in relevance_ranked:
                        # Extract the link text and format it
                        link_text = link.split('/')[-1].replace('_', ' ')
                        
                        # Generate HTML for the link and relevance score
                        link_html = f'<a href="https://en.wikipedia.org{link}">{link_text}</a> : {relevance_score}<br>'
                        
                        # Append to the overall HTML code
                        links_html += link_html

                    # Print or use the generated HTML code
                    #print("links_html: ", links_html)
                    return links_html
                
                except ValueError:
                    print("Invalid relevance_ranked format: could not evaluate as a list.")

    except Exception as e:
        print("An error occurred:", str(e))
        return []


# Web Scraping with BeautifulSoup
async def webScraping(wikilink):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(wikilink) as response:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')

                # Your web scraping logic here

                # Find all anchor elements with href starting with '/wiki/'
                links = soup.find_all('a', href=lambda href: href and href.startswith('/wiki/'))
                
                # Extract the href attribute value for each link
                internal_wikis = [link['href'] for link in links]

                # Remove unwanted elements
                unwanted_ids = ['right-navigation', 'vector-toc', 'vector-page-titlebar-toc', 'p-lang-btn', 'footer-icons']
                for unwanted_id in unwanted_ids:
                    unwanted_elem = soup.find(id=unwanted_id)
                    if unwanted_elem:
                        unwanted_elem.decompose()

                # Remove elements with aria-label="Namespaces"
                unwanted_aria = soup.find_all(attrs={"aria-label": "Namespaces"})
                for elem in unwanted_aria:
                    elem.decompose()

                # Check if the start tag exists
                start_element = soup.find(class_="mw-page-container")
                if start_element:
                    # Extract the HTML content starting from the start tag
                    content = str(start_element)
                else:
                    content = str(soup)

                return content, internal_wikis
    except aiohttp.ClientError as e:
        logger.error(f"Error scraping website: {e}")
        return None, None


async def checkDbWebScrape(wikilink):
    # Extract page name from the URL
    page_name = urlparse(wikilink).path.split('/')[-1]

    try:
        # Check if data exists in the database
        content = check_database(page_name, 'content')
        if content:
            logger.info("Data found in the database")
            return content, ""
        else:
            logger.info("Data not found in the database, scraping website...")
            # Data not found, perform web scraping
            content, internal_wikis = await webScraping(wikilink)
            if content:
                # Save data to the database
                logger.info("Saving wikilink, page_name, and content data to database...")
                await save_to_database_async(wikilink, page_name, content, None)
            else:
                logger.error("Failed to retrieve content from Wikipedia")
    except Exception as e:
        logger.error(f"Error in checkDbWebScrape: {e}")

    return content, internal_wikis


app = Flask(__name__)
CORS(app)  # Initialize Flask-CORS with your Flask application instance

@app.route('/server/process_form', methods=['GET'])
async def process_form():
    initialize_database()
    global start_time, internal_wikis
    start_time = time.time()  # Record the start time

    # Process form data and retrieve initial content
    wikilink = request.args.get('wikilink', '')
    content, internal_wikis = await checkDbWebScrape(wikilink)

    # Return initial content as JSON response with CORS headers
    response_data = {'content': content}
    response = jsonify(response_data)

    end_time = time.time()  # Record the end time
    duration = end_time - start_time  # Calculate the duration
    logger.info(f"Request processed in {duration:.2f} seconds")

    return response


@app.route('/server/get_relevance_ranked', methods=['GET'])
async def get_relevance_ranked():
    # Fetch relevance_ranked asynchronously
    wikilink = request.args.get('wikilink', '')
    # Extract page name from the URL
    page_name = urlparse(wikilink).path.split('/')[-1]

    # Check if data exists in the database
    relevance_ranked = check_database(page_name, 'relevance_ranked')

    if not relevance_ranked:    
        relevance_ranked = await webScrapingAPI(wikilink, internal_wikis)

        # Save data to the database
        logger.info("Saving relevance_ranked data to database...")
        await save_to_database_async(wikilink, page_name, '' , str(relevance_ranked))

    # Modify the response content to include "Related Internal Links"
    response_content = "<br><h1>Related Internal Links</h1>"
    response_content += relevance_ranked
    
    # Return relevance_ranked data as JSON response with CORS headers
    response_data = {'relevance_ranked': response_content}

    response = jsonify(response_data)

    end_time = time.time()  # Record the end time
    duration = end_time - start_time  # Calculate the duration
    logger.info(f"Request processed in {duration:.2f} seconds")

    return response

if __name__ == '__main__':
    app.run(port=8000,debug=True)