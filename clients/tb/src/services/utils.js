/**
 * Utilities that are shared across pages
 */

import rpcs from '@/services/rpc-service'
import status from '@/services/status-service'

function dcp(input) {
  var output = JSON.parse(JSON.stringify(input))
  return output
}

function sleep(time) {
  // Return a promise that resolves after _time_ milliseconds.
  return new Promise((resolve) => setTimeout(resolve, time));
}

function getUniqueName(fileName, otherNames) {
  let tryName = fileName
  let numAdded = 0
  while (otherNames.indexOf(tryName) > -1) {
    numAdded = numAdded + 1
    tryName = fileName + ' (' + numAdded + ')'
  }
  return tryName
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

function makeGraphs(vm) {
  console.log('makeGraphs() called')
  status.start(vm) // Start indicating progress.
  var n_plots = vm.response.data.graphs.length
  console.log('Rendering ' + n_plots + ' graphs')
  for (var index = 0; index <= n_plots; index++) {
    console.log('Rendering plot ' + index)
    var divlabel = 'fig' + index
    var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
    while (div.firstChild) {
      div.removeChild(div.firstChild);
    }
    try {
      console.log(vm.response.data.graphs[index]);
      mpld3.draw_figure(divlabel, vm.response.data.graphs[index], function(fig, element) {
        fig.setXTicks(6, function(d) { return d3.format('.0f')(d); });
        fig.setYTicks(null, function(d) { return d3.format('.2s')(d); });
      });
      vm.haveDrawnGraphs = true
    }
    catch (error) {
      console.log('Making graphs failed: ' + error.message);
    }
  }
  status.succeed(vm, 'Graphs created') // Indicate success.
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
  dcp,
  sleep,
  getUniqueName,
  placeholders,
  projectID,
  hasData,
  simStart,
  simEnd,
  makeGraphs,
  clearGraphs,
  exportResults,
}