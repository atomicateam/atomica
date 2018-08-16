/**
 * Shared services that don't fit anywhere else!
 */

function sleep(time) {
  // Return a promise that resolves after _time_ milliseconds.
  return new Promise((resolve) => setTimeout(resolve, time));
}

function placeholders() {
  var indices = []
  for (var i = 0; i <= 100; i++) {
    indices.push(i);
  }
  return indices;
}

function projectID(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    let projectID = vm.$store.state.activeProject.project.id
    return projectID
  }
}

function hasData(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return false
  }
  else {
    return vm.$store.state.activeProject.project.hasData
  }
}

function simStart(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    return vm.$store.state.activeProject.project.sim_start
  }
}

function simEnd(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    return vm.$store.state.activeProject.project.sim_end
  }
}

function clearGraphs() {
  for (var index = 0; index <= 100; index++) {
    console.log('Clearing plot ' + index)
    var divlabel = 'fig' + index
    var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
    while (div.firstChild) {
      div.removeChild(div.firstChild);
    }
  }
}

function exportResults(vm, project_id) {
  console.log('exportResults() called')
  rpcs.download('export_results', [project_id]) // Make the server call to download the framework to a .prj file.
    .catch(error => {
    status.failurePopup(vm, 'Could not export results')
})
}

export default {
  sleep,
  placeholders,
  projectID,
  hasData,
  simStart,
  simEnd,
  clearGraphs,
  exportResults,
}