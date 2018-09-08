/**
 * Utilities that are shared across pages
 */

import rpcs from '@/services/rpc-service'
import status from '@/services/status-service'

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

function projectID(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  }
  else {
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

function hasPrograms(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return false
  }
  else {
    return vm.$store.state.activeProject.project.hasPrograms
  }
}

function simStart(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  }
  else {
    return vm.$store.state.activeProject.project.sim_start
  }
}

function simEnd(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  }
  else {
    return vm.$store.state.activeProject.project.sim_end
  }
}

function simYears(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return []
  }
  else {
    var sim_start = vm.$store.state.activeProject.project.sim_start
    var sim_end = vm.$store.state.activeProject.project.sim_end
    var years = []
    for (var i = sim_start; i <= sim_end; i++) {
      years.push(i);
    }
    console.log('sim years: ' + years)
    return years;
  }
}

function activePops(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  }
  else {
    let pop_pairs = vm.$store.state.activeProject.project.pops
    let pop_list = ["All"]
    for(let i = 0; i < pop_pairs.length; ++i) {
      pop_list.push(pop_pairs[i][1]);
    }
    return pop_list
  }
}

function getPlotOptions(vm) {
  return new Promise((resolve, reject) => {
    console.log('getPlotOptions() called')
    status.start(vm) // Start indicating progress.
    let project_id = projectID(vm)
    rpcs.rpc('get_supported_plots', [project_id, true])
    .then(response => {
      vm.plotOptions = response.data // Get the parameter values
      status.succeed(vm, '')
      resolve(response)
    })
    .catch(error => {
      status.fail(vm, 'Could not get plot options: ' + error.message)
      reject(error)
    })          
  })
}

function placeholders(vm, startVal) {
  var indices = []
  if (!startVal) {
    startVal = 0
  }
  for (var i = startVal; i <= 100; i++) {
    indices.push(i);
    vm.showGraphDivs[i] = false
    vm.showLegendDivs[i] = false
  }
  return indices;
}

function makeGraphs(vm, graphdata) {
  let waitingtime = 0.5
  console.log('makeGraphs() called')
  status.start(vm) // Start indicating progress.
  vm.hasGraphs = true
  sleep(waitingtime * 1000)
  .then(response => {
    let n_plots = graphdata.length
    console.log('Rendering ' + n_plots + ' graphs')
    for (var index = 0; index <= n_plots; index++) {
      console.log('Rendering plot ' + index)

      var figlabel    = 'fig' + index
      console.log(figlabel)
      var figdiv  = document.getElementById(figlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
      console.log(figdiv)
      while (figdiv.firstChild) {
        figdiv.removeChild(figdiv.firstChild);
      }
      console.log('new_1');

      if (index>=1 && index<n_plots) {
        // var containerlabel = 'container' + index
        // var containerdiv = document.getElementById(containerlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
        // containerdiv.style.display = 'flex'

        console.log('new_2');
        var legendlabel = 'legend' + index
        var legenddiv  = document.getElementById(legendlabel);
        while (legenddiv.firstChild) {
          legenddiv.removeChild(legenddiv.firstChild);
        }
        console.log('new_3');
        // minimize(vm, index) // As soon as we've created a plot, minimize it
        console.log('new_4');

        console.log('div review')
        console.log(figdiv)
        // console.log(containerdiv)
        // console.log(legenddiv)
      }

      console.log('hi_1');
      vm.showGraphDivs[index] = true;
      console.log('hi_2');
      mpld3.draw_figure(figlabel, graphdata[index], function (fig, element) {
        console.log('hi_3');
        fig.setXTicks(6, function (d) {
          return d3.format('.0f')(d);
        });
        console.log('hi_4');
        fig.setYTicks(null, function (d) {
          return d3.format('.2s')(d);
        });
      });
      if (index>=1 && index<n_plots) {
        mpld3.draw_figure(legendlabel, graphdata[index], function (fig, element) {
          console.log('hi_5');
          fig.setXTicks(6, function (d) {
            return d3.format('.0f')(d);
          });
          console.log('hi_6');
          fig.setYTicks(null, function (d) {
            return d3.format('.2s')(d);
          });
        });
      }
    }
  status.succeed(vm, 'Graphs created') // CK: This should be a promise, otherwise this appears before the graphs do
  })
}

function clearGraphs(vm) {
  for (var index = 0; index <= 100; index++) {
    var divlabel = 'fig' + index
    var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
    while (div.firstChild) {
      div.removeChild(div.firstChild);
    }
    vm.hasGraphs = false
  }
}

function exportGraphs(vm) {
  return new Promise((resolve, reject) => {
    console.log('exportGraphs() called')
    rpcs.download('download_graphs', [])
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


//
// Graphs DOM functions
//

function showBrowserWindowSize() {
  var w = window.innerWidth;
  var h = window.innerHeight;
  var ow = window.outerWidth; //including toolbars and status bar etc.
  var oh = window.outerHeight;
  console.log('Browser window size:')
  console.log(w, h, ow, oh)
}

function scaleElem(svg, frac) {
  // It might ultimately be better to redraw the graph, but this works
  var width  = svg.getAttribute("width")
  var height = svg.getAttribute("height")
  var viewBox = svg.getAttribute("viewBox")
  if (!viewBox) {
    svg.setAttribute("viewBox",  '0 0 ' + width + ' ' + height)
  }
  // if this causes the image to look weird, you may want to look at "preserveAspectRatio" attribute
  svg.setAttribute("width",  width*frac)
  svg.setAttribute("height", height*frac)
}

function scaleFigs(frac) {
  var graphs = window.top.document.querySelectorAll('svg.mpld3-figure')
  for (var g = 0; g < graphs.length; g++) {
    scaleElem(graphs[g], frac)
  }
}



//
// Legend functions
// 



function addListener(vm) {
  document.addEventListener('mousemove', function(e){onMouseUpdate(e, vm)}, false);
}



function onMouseUpdate(e, vm) {
  vm.mousex = e.pageX;
  vm.mousey = e.pageY;
  // console.log(vm.mousex, vm.mousey)
}

function createDialogs(vm) {
  var vals = placeholders(vm)
  for (var val in vals) {
    newDialog(vm, val, 'Dialog '+val, 'This is test '+val)
  }
}

// Create a new dialog
function newDialog(vm, id, name, content) {
  let options = {}
  let properties = { id, name, content, options }
  return vm.openDialogs.push(properties)
}

function findDialog(vm, id, dialogs) {
  let index = dialogs.findIndex((val) => {
      return String(val.id) === String(id) // Force type conversion
    })
  return (index > -1) ? index : null
}

// "Show" the dialog
function maximize(vm,id) {
  console.log('maximizing')
  console.log(id)
  console.log(Number(id))
  console.log(vm.showLegendDivs[Number(id)])
  vm.showLegendDivs[Number(id)] = false
  var containerlabel = 'legendcontainer'+id
  console.log(containerlabel)
  var containerdiv  = document.getElementById(containerlabel);
  console.log(containerdiv)
  containerdiv.style.display = 'inline-block' // Ensure they're visible
  console.log(vm.showLegendDivs[Number(id)])
  console.log('ok')
  // let index = findDialog(vm, id, vm.openDialogs)
  // if (index !== null) {
  //   vm.openDialogs[index].options.left = vm.mousex-80 // Before opening, move it to where the mouse currently is
  //   vm.openDialogs[index].options.top = vm.mousey-300
  //   // vm.openDialogs.push(vm.closedDialogs[index])
  //   // vm.closedDialogs.splice(index, 1)
  // }
  // var dialogcontainerdiv  = document.getElementById('dialogcontainer');
  // dialogcontainerdiv.style.display = 'block' // Ensure they're visible
}

// "Hide" the dialog
function minimize(vm, id) {
  console.log('minimizing')
  console.log(id)
  console.log(Number(id))
  console.log(vm.showLegendDivs[Number(id)])
  vm.showLegendDivs[Number(id)] = false
  var containerlabel = 'legendcontainer'+id
  console.log(containerlabel)
  var containerdiv  = document.getElementById(containerlabel);
  console.log(containerdiv)
  containerdiv.style.display = 'none' // Ensure they're invisible
  console.log(vm.showLegendDivs[Number(id)])
  console.log('ok')
  // let index = findDialog(vm, id, vm.openDialogs)
  // if (index !== null) {
    // vm.closedDialogs.push(vm.openDialogs[index])
    // vm.openDialogs.splice(index, 1)
  // }
}


export default {
  sleep,
  getUniqueName,
  placeholders,
  projectID,
  hasData,
  hasPrograms,
  simStart,
  simEnd,
  simYears,
  activePops,
  getPlotOptions,
  makeGraphs,
  clearGraphs,
  exportGraphs,
  exportResults,
  scaleFigs,
  showBrowserWindowSize,

  addListener,
  onMouseUpdate,
  createDialogs,
  newDialog,
  findDialog,
  maximize,
  minimize
  
}