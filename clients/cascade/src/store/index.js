// index.js -- Vuex store configuration
//
// Last update: 3/7/18 (gchadder3)

import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    // The currently logged in user
    currentUser: {}, 

    // The project currently chosen by the user
    activeProject: {}
  },

  mutations: {
    newUser(state, user) {
      state.currentUser = user
    }, 

    newActiveProject(state, project) {
      state.activeProject = project
    }
  }
})
export default store