/*
 * Small utilities that are shared across pages
 */

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

function validateYears(vm) {
  if      (vm.startYear > vm.simEnd)   { vm.startYear = vm.simEnd }
  else if (vm.startYear < vm.simStart) { vm.startYear = vm.simStart }
  if      (vm.endYear   > vm.simEnd)   { vm.endYear   = vm.simEnd }
  else if (vm.endYear   < vm.simStart) { vm.endYear   = vm.simStart }
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

function simYears(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return []
  } else {
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

function dataStart(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    return vm.$store.state.activeProject.project.data_start
  }
}

function dataEnd(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    console.log('dataEnd: ' + vm.$store.state.activeProject.project.data_end)
    return vm.$store.state.activeProject.project.data_end
  }
}

function dataYears(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return []
  } else {
    let data_start = vm.$store.state.activeProject.project.data_start
    let data_end = vm.$store.state.activeProject.project.data_end
    let years = []
    for (let i = data_start; i <= data_end; i++) {
      years.push(i);
    }
    console.log('data years: ' + years)
    return years;
  }
}

// projection years are used for scenario and optimization plot year dropdowns
function projectionYears(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return []
  } else {
    let data_end = vm.$store.state.activeProject.project.data_end
    let sim_end = vm.$store.state.activeProject.project.sim_end
    let years = []
    for (let i = data_end; i <= sim_end; i++) {
      years.push(i);
    }
    console.log('projection years: ' + years)
    return years;
  }
}

function activePops(vm) {
  if (vm.$store.state.activeProject.project === undefined) {
    return ''
  } else {
    let pop_pairs = vm.$store.state.activeProject.project.pops
    let pop_list = ["All"]
    for(let i = 0; i < pop_pairs.length; ++i) {
      pop_list.push(pop_pairs[i][1]);
    }
    return pop_list
  }
}


function updateSorting(vm, sortColumn) {
  console.log('updateSorting() called')
  if (vm.sortColumn === sortColumn) { // If the active sorting column is clicked...
    vm.sortReverse = !vm.sortReverse // Reverse the sort.
  } else { // Otherwise.
    vm.sortColumn = sortColumn // Select the new column for sorting.
    vm.sortReverse = false // Set the sorting for non-reverse.
  }
}


export default {
  sleep,
  getUniqueName,
  validateYears,
  projectID,
  hasData,
  hasPrograms,
  simStart,
  simEnd,
  simYears,
  dataStart,
  dataEnd,
  dataYears,
  projectionYears,
  activePops,
  updateSorting,
}