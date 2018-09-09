/*
 * Graphing functions (shared between calibration, scenarios, and optimization)
 */

import utils from '@/js/utils'
import rpcs from '@/js/rpc-service'
import status from '@/js/status-service'

function getPlotOptions(vm, project_id) {
  return new Promise((resolve, reject) => {
    console.log('getPlotOptions() called')
    status.start(vm) // Start indicating progress.
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

function togglePlotControls(vm) {
  vm.showPlotControls = !vm.showPlotControls
}

function placeholders(vm, startVal) {
  let indices = []
  if (!startVal) {
    startVal = 0
  }
  for (let i = startVal; i <= 100; i++) {
    indices.push(i);
    vm.showGraphDivs.push(false);
    vm.showLegendDivs.push(false);
  }
  return indices;
}

function clearGraphs(vm) {
  for (let index = 0; index <= 100; index++) {
    let divlabel = 'fig' + index
    let div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
    while (div.firstChild) {
      div.removeChild(div.firstChild);
    }
    vm.hasGraphs = false
  }
}

function makeGraphs(vm, data) {
  let waitingtime = 0.5
  console.log('makeGraphs() called')
  var graphdata = data.graphs
  var legenddata = data.legends
  status.start(vm) // Start indicating progress.
  vm.hasGraphs = true
  utils.sleep(waitingtime * 1000)
  .then(response => {
    let n_plots = graphdata.length
    let n_legends = legenddata.length
    console.log('Rendering ' + n_plots + ' graphs')
    if (n_plots !== n_legends) {
      console.log('WARNING: different numbers of plots and legends: ' + n_plots + ' vs. ' + n_legends)
    }
    for (var index = 0; index <= n_plots; index++) {
      console.log('Rendering plot ' + index)
      var figlabel    = 'fig' + index
      var figdiv  = document.getElementById(figlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
      if (figdiv) {
        while (figdiv.firstChild) {
          figdiv.removeChild(figdiv.firstChild);
        }
      } else {
        console.log('WARNING: figdiv not found: ' + figlabel)
      }

      // Show figure containers
      if (index>=1 && index<n_plots) {
        var figcontainerlabel = 'figcontainer' + index
        var figcontainerdiv = document.getElementById(figcontainerlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
        if (figcontainerdiv) {
          figcontainerdiv.style.display = 'flex'
        } else {
          console.log('WARNING: figcontainerdiv not found: ' + figcontainerlabel)
        }

        var legendlabel = 'legend' + index
        var legenddiv  = document.getElementById(legendlabel);
        if (legenddiv) {
          while (legenddiv.firstChild) {
            legenddiv.removeChild(legenddiv.firstChild);
          }
        } else {
          console.log('WARNING: legenddiv not found: ' + legendlabel)
        }
      }

      // Draw figures
      mpld3.draw_figure(figlabel, graphdata[index], function (fig, element) {
        fig.setXTicks(6, function (d) {
          return d3.format('.0f')(d);
        });
        fig.setYTicks(null, function (d) {
          return d3.format('.2s')(d);
        });
      });

      // Draw legends
      if (index>=1 && index<n_plots) {
        mpld3.draw_figure(legendlabel, legenddata[index], function (fig, element) {
          fig.setXTicks(6, function (d) {
            return d3.format('.0f')(d);
          });
          fig.setYTicks(null, function (d) {
            return d3.format('.2s')(d);
          });
        });
      }
      vm.showGraphDivs[index] = true;
    }
  status.succeed(vm, 'Graphs created') // CK: This should be a promise, otherwise this appears before the graphs do
  })
}


function reloadGraphs(vm, showNoCacheError, iscalibration) {
  console.log('plotCalibration() called')
  vm.validateYears()  // Make sure the start end years are in the right range.
  status.start(this)
  rpcs.rpc('plot_results_cache_entry', [vm.projectID, vm.serverDatastoreId, vm.plotOptions],
    {tool:vm.$globaltool, 'cascade':null, plotyear:vm.endYear, pops:vm.activePop, calibration:iscalibration})
    .then(response => {
      vm.makeGraphs(response.data)
      vm.table = response.data.table
      status.succeed(this, 'Data loaded, graphs now rendering...')
    })
    .catch(error => {
      if (showNoCacheError) {
        status.fail(this, 'Could not make graphs', error)
      }
      else {
        status.succeed(this, '')  // Silently stop progress bar and spinner.
      }
    })
}

//
// Graphs DOM functions
//

function showBrowserWindowSize() {
  let w = window.innerWidth;
  let h = window.innerHeight;
  let ow = window.outerWidth; //including toolbars and status bar etc.
  let oh = window.outerHeight;
  console.log('Browser window size:')
  console.log(w, h, ow, oh)
}

function scaleElem(svg, frac) {
  // It might ultimately be better to redraw the graph, but this works
  let width  = svg.getAttribute("width")
  let height = svg.getAttribute("height")
  let viewBox = svg.getAttribute("viewBox")
  if (!viewBox) {
    svg.setAttribute("viewBox",  '0 0 ' + width + ' ' + height)
  }
  // if this causes the image to look weird, you may want to look at "preserveAspectRatio" attribute
  svg.setAttribute("width",  width*frac)
  svg.setAttribute("height", height*frac)
}

function scaleFigs(vm, frac) {
  vm.figscale = vm.figscale*frac;
  if (frac === 1.0) {
    frac = 1.0/vm.figscale
    vm.figscale = 1.0
  }
  let graphs = window.top.document.querySelectorAll('svg.mpld3-figure')
  for (let g = 0; g < graphs.length; g++) {
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
  let vals = placeholders(vm)
  for (let val in vals) {
    newDialog(vm, val, 'Dialog '+val, 'This is test '+val)
  }
}

// Create a new dialog
function newDialog(vm, id, name, content) {
  let options = {left:123+Number(id), top:123}
  let style = {options:options}
  let properties = { id, name, content, style, options }
  return vm.openDialogs.push(properties)
}

function findDialog(vm, id, dialogs) {
  console.log('looking')
  let index = dialogs.findIndex((val) => {
      return String(val.id) === String(id) // Force type conversion
    })
  return (index > -1) ? index : null
}

// "Show" the dialog
function maximize(vm,id) {
  let index = Number(id)
  let DDlabel = 'DD'+id // DD for dialog-drag
  let DDdiv  = document.getElementById(DDlabel);
  if (DDdiv) {
    DDdiv.style.left = String(vm.mousex-80) + 'px'
    DDdiv.style.top = String(vm.mousey-300) + 'px'
  } else {
    console.log('WARNING: DDdiv not found: ' + DDlabel)
  }
  if (index !== null) {
    vm.openDialogs[index].options.left = vm.mousex-80 // Before opening, move it to where the mouse currently is
    vm.openDialogs[index].options.top = vm.mousey-300
  }
  vm.showLegendDivs[index] = true // Not really used, but here for completeness
  let containerlabel = 'legendcontainer'+id
  let containerdiv  = document.getElementById(containerlabel);
  if (containerdiv) {
    containerdiv.style.display = 'inline-block' // Ensure they're invisible
  } else {
    console.log('WARNING: containerdiv not found: ' + containerlabel)
  }
}

// "Hide" the dialog
function minimize(vm, id) {
  let index = Number(id)
  vm.showLegendDivs[index] = false
  let containerlabel = 'legendcontainer'+id
  let containerdiv  = document.getElementById(containerlabel);
  if (containerdiv) {
    containerdiv.style.display = 'none' // Ensure they're invisible
  } else {
    console.log('WARNING: containerdiv not found: ' + containerlabel)
  }
}

export default {
  placeholders,
  clearGraphs,
  getPlotOptions,
  togglePlotControls,
  makeGraphs,
  reloadGraphs,
  scaleFigs,
  showBrowserWindowSize,
  addListener,
  onMouseUpdate,
  createDialogs,
  newDialog,
  findDialog,
  maximize,
  minimize,
}