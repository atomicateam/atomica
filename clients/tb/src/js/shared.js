/*
 * Heftier functions that are shared across pages
 */


function exportGraphs(vm, serverDatastoreId) {
  return new Promise((resolve, reject) => {
    console.log('exportGraphs() called')
    rpcs.download('download_graphs', [serverDatastoreId])
      .then(response => {
        resolve(response)
      })
      .catch(error => {
        status.failurePopup(vm, 'Could not download graphs: ' + error.message)
        reject(error)
      })
  })
}

function exportResults(vm, serverDatastoreId) {
  return new Promise((resolve, reject) => {
    console.log('exportResults() called TEMP FIX')
    rpcs.download('export_results', [serverDatastoreId])
      .then(response => {
        resolve(response)
      })
      .catch(error => {
        status.failurePopup(vm, 'Could not export results: ' + error.message)
        reject(error)
      })
  })
}

export default {
  exportGraphs,
  exportResults,
}