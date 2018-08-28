// rpc-service.js -- RPC functions for Vue to call
//
// Last update: 2018aug26

import axios from 'axios'
var filesaver = require('file-saver')
var CryptoApi = require('crypto-api')

// consoleLogCommand() -- Print an RPC call to the browser console.
function consoleLogCommand (type, funcname, args, kwargs) {
  if (!args) { // Don't show any arguments if none are passed in.
    args = ''
  }
  if (!kwargs) { // Don't show any kwargs if none are passed in.
    kwargs = ''
  }
  console.log("RPC service call (" + type + "): " + funcname, args, kwargs)
}

// readJsonFromBlob(theBlob) -- Attempt to convert a Blob passed in to a JSON. Passes back a Promise.
function readJsonFromBlob(theBlob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader() // Create a FileReader; reader.result contains the contents of blob as text when this is called
    reader.addEventListener("loadend", function() { // Create a callback for after the load attempt is finished
      try { // Call a resolve passing back a JSON version of this.
        var jsonresult = JSON.parse(reader.result) // Try the conversion.
        resolve(jsonresult) // (Assuming successful) make the Promise resolve with the JSON result.
      } catch (e) {
        reject(Error('Failed to convert blob to JSON')) // On failure to convert to JSON, reject the Promise.
      }
    })
    reader.readAsText(theBlob) // Start the load attempt, trying to read the blob in as text.
  })
}

export default {
  rpc(funcname, args, kwargs) { // rpc() -- normalRPC() /api/procedure calls in api.py.
    consoleLogCommand("normal", funcname, args, kwargs) // Log the RPC call.
    return new Promise((resolve, reject) => { // Do the RPC processing, returning results as a Promise.
      axios.post('/api/rpcs', { // Send the POST request for the RPC call.
        funcname: funcname, 
        args: args, 
        kwargs: kwargs
      })
      .then(response => {
        if (typeof(response.data.error) != 'undefined') { // If there is an error in the POST response.
          reject(Error(response.data.error))
        }
        resolve(response) // Signal success with the response.
      })
      .catch(error => {
        if (error.response) { // If there was an actual response returned from the server...
          if (typeof(error.response.data.exception) != 'undefined') { // If we have exception information in the response (which indicates an exception on the server side)...
            reject(Error(error.response.data.exception)) // For now, reject with an error message matching the exception.
          }
        }
        reject(error) // Reject with the error axios got.
      })
    })
  },

  download(funcname, args, kwargs) { // download() -- download() /api/download calls in api.py.
    consoleLogCommand("download", funcname, args, kwargs) // Log the download RPC call.
    return new Promise((resolve, reject) => { // Do the RPC processing, returning results as a Promise.
      axios.post('/api/rpcs', { // Send the POST request for the RPC call.
        funcname: funcname, 
        args: args, 
        kwargs: kwargs
      }, 
      {
        responseType: 'blob'
      })
      .then(response => {
        readJsonFromBlob(response.data)
        .then(responsedata => {
          if (typeof(responsedata.error) != 'undefined') { // If we have error information in the response (which indicates a logical error on the server side)...
            reject(Error(responsedata.error)) // For now, reject with an error message matching the error.
          }
        })
        .catch(error2 => { // An error here indicates we do in fact have a file to download.
          var blob = new Blob([response.data]) // Create a new blob object (containing the file data) from the response.data component.
          var filename = response.headers.filename // Grab the file name from response.headers.
          filesaver.saveAs(blob, filename) // Bring up the browser dialog allowing the user to save the file or cancel doing so.
          resolve(response) // Signal success with the response.
        })
      })
      .catch(error => {
        if (error.response) { // If there was an actual response returned from the server...
          readJsonFromBlob(error.response.data)
          .then(responsedata => {
            if (typeof(responsedata.exception) != 'undefined') { // If we have exception information in the response (which indicates an exception on the server side)...
              reject(Error(responsedata.exception)) // For now, reject with an error message matching the exception.
            }
          })
          .catch(error2 => {
            reject(error) // Reject with the error axios got.
          })
        } else {
          reject(error) // Otherwise (no response was delivered), reject with the error axios got.
        }
      })
    })
  },

  // upload() -- upload() /api/upload calls in api.py.
  upload(funcname, args, kwargs, fileType) {
    consoleLogCommand("upload", funcname, args, kwargs) // Log the upload RPC call.
    return new Promise((resolve, reject) => { // Do the RPC processing, returning results as a Promise.
      var onFileChange = (e) => { // Function for trapping the change event that has the user-selected file.
        var files = e.target.files || e.dataTransfer.files // Pull out the files (should only be 1) that were selected.
        if (!files.length) // If no files were selected, reject the promise.
          reject(Error('No file selected'))
        const formData = new FormData() // Create a FormData object for holding the file.
        formData.append('uploadfile', files[0]) // Put the selected file in the formData object with 'uploadfile' key.
        formData.append('funcname', funcname) // Add the RPC function name to the form data.
        formData.append('args', JSON.stringify(args)) // Add args and kwargs to the form data.
        formData.append('kwargs', JSON.stringify(kwargs))
        axios.post('/api/rpcs', formData) // Use a POST request to pass along file to the server.
        .then(response => {
          // If there is an error in the POST response.
          if (typeof(response.data.error) != 'undefined') {
            reject(Error(response.data.error))
          }
          resolve(response) // Signal success with the response.
        })
        .catch(error => {
          if (error.response) { // If there was an actual response returned from the server...
            if (typeof(error.response.data.exception) != 'undefined') { // If we have exception information in the response (which indicates an exception on the server side)...
              reject(Error(error.response.data.exception)) // For now, reject with an error message matching the exception.
            }
          }
          reject(error) // Reject with the error axios got.
        })
      }

      // Create an invisible file input element and set its change callback to our onFileChange function.
      var inElem = document.createElement('input')
      inElem.setAttribute('type', 'file')
      inElem.setAttribute('accept', fileType)
      inElem.addEventListener('change', onFileChange)
      inElem.click() // Manually click the button to open the file dialog.
    })
  }
}