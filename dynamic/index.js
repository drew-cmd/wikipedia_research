document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById("wikiForm");
  const responseDiv = document.getElementById('response');
  const radioYes = document.getElementById('radioYes');
  const radioNo = document.getElementById('radioNo');

  form.addEventListener('submit', function(event) {
      event.preventDefault();

      const wikilinkValue = document.getElementById('wikilink').value;
      let checkValue;
      if (radioYes.checked) {
          checkValue = 1;
      } else if (radioNo.checked) {
          checkValue = 0;
      } else {
          checkValue = 0;
      }

      const queryString = `wikilink=${encodeURIComponent(wikilinkValue)}&check=${encodeURIComponent(checkValue)}`;

      // Send the AJAX request to the Flask server to process form data
      fetch('http://localhost:8000/server/process_form?' + queryString, {
          method: 'GET',
      })
      .then(function(response) {
          if (!response.ok) {
              throw new Error('Network response was not ok');
          }
          return response.json();
      })
      .then(function(data) {
          // Update the responseDiv with the initial content
          responseDiv.innerHTML = data.content;

          if (checkValue == 1) {
            // Make another AJAX request to fetch relevance_ranked data
            fetch('http://localhost:8000/server/get_relevance_ranked?' + queryString, {
            method: 'GET',
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(function(data) {
                // Update the responseDiv with the relevance_ranked data
                responseDiv.innerHTML += data.relevance_ranked;
            })
            .catch(function(error) {
                console.error('There was a problem fetching relevance-ranked data:', error);
                responseDiv.innerHTML += 'An error occurred while fetching relevance-ranked data.';
            });
          }
      })
      .catch(function(error) {
          console.error('There was a problem submitting the form:', error);
          responseDiv.innerHTML = 'An error occurred while submitting the form. Please try again later.';
      });
  });
});
