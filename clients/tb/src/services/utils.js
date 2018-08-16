/**
 * Shared services that don't fit anywhere else!
 */

function sleep(time) {
  // Return a promise that resolves after _time_ milliseconds.
  return new Promise((resolve) => setTimeout(resolve, time));
}


export default {
  sleep
}