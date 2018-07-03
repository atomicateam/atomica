// index.js -- Vuex store configuration
//
// Last update: 3/7/18 (gchadder3)

import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    currentUser: {},  // The currently logged in user
    activeProject: {}, // The project currently chosen by the user
    activeFramework: {} // The framework currently chosen by the user
  },

  mutations: {
    newUser(state, user) {
      state.currentUser = user
    }, 

    newActiveFramework(state, framework) {
      state.activeFramework = framework
    },

    newActiveProject(state, project) {
      state.activeProject = project
    }
  }
})
export default store