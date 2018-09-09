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
    let sim_start = vm.$store.state.activeProject.project.sim_start
    let sim_end = vm.$store.state.activeProject.project.sim_end
    let years = []
    for (let i = sim_start; i <= sim_end; i++) {
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

export default {
  sleep,
  getUniqueName,
  projectID,
  hasData,
  hasPrograms,
  simStart,
  simEnd,
  simYears,
  activePops,
}