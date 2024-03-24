# wikipedia_research

Webscrapes user inputted Wikipedia articles, returns content, and saves content to a database for faster future retrieval.

Locally hosted website to take in user input (in this case Wikipedia URLs) and send the request to a server whereby content from the Wiki page is returned. 

Server operations included some URL validation, checking for already existing content in a database (searched by Wiki page name), website web scraping and formatting via BeautifulSoup, saving content to a database, querying ChatGPT via the Python ChatGPT API to rank a list of webscraped internal Wikipedia links in order of relevance to the Wikipedia URL provided, and returning the content to be displayed to the user on the webpage.

#### Front End

HTML, CSS, and JavaScript.

#### Back End

Python (includes database reading and writing component with built-in SQLite).

## Description of Server code:

Takes in user inputted Wikipedia URL as well as indicated as to whether to return rankings for internal wiki links.

Webscrapes content and internal wiki links from the Wikipedia page.

Saves wiklink, page_name, and content to the database for future, faster retrieval.

If prompted for rankings of internal wiki links, will send prompt to ChatGPT via Python ChatGPT API to rank provided internal wiki links in order of relevance to the user inputted Wikipedia URL.

The returned data will then be saved to the appropriate row of the database in the relevance_ranked column.

## Included Folders:

#### Static

Includes HTML and CSS files for displaying the website and minamally stylizing it. Used built in VS Code Live Server extension to run the website live on a local machine.

#### Dynamic

Includes JavaScript code which listens to events, passes user input to server, and returns the server response to the website to be displayed.

#### Server

Includes Python server and database which takes the client request, breaks it up, validates it, checks the page against the database, and web scrapes the Wikipedia page for content if it is not found in the database. The content is then saved to the database along with the wiki link and wiki page name for later quicker retrieval and the web scraped content is returned to the client.

#### settings.json

The Live Server VS Code extension caused issues where its live reloading feature would cause the client page to reload following every initial request to the server when web scraped wikipedia page content was saved to the database. It would then display and not reload on a subsequent request of the same Wikipedia page. To prevent this feature, code was included in this file to ignore the extension's live reloading feature. 
