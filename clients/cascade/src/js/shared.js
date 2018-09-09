/*
 * Heftier functions that are shared across pages
 */


function validateYears(vm) {
  if      (vm.startYear > vm.simEnd)   { vm.startYear = vm.simEnd }
  else if (vm.startYear < vm.simStart) { vm.startYear = vm.simStart }
  if      (vm.endYear   > vm.simEnd)   { vm.endYear   = vm.simEnd }
  else if (vm.endYear   < vm.simStart) { vm.endYear   = vm.simStart }
}

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
  validateYears,
  exportGraphs,
  exportResults,
}