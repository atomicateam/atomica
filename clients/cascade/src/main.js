// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
// Plugins
// Simple alert plugin
import Simplert from 'vue2-simplert-plugin'
require('vue2-simplert-plugin/dist/vue2-simplert-plugin.css')

import GlobalComponents from './globalComponents'
import GlobalDirectives from './globalDirectives'
import Notifications from './components/generic/NotificationPlugin'
import SideBar from './components/app/Sidebar'
import App from './App'
import router from './router'
import store from './store'

Vue.config.productionTip = false
// library imports
import Chartist from 'chartist'
import 'bootstrap/dist/css/bootstrap.css'
import './assets/sass/project.scss'
import 'es6-promise/auto'

// plugin setup
Vue.use(GlobalComponents);
Vue.use(GlobalDirectives);
Vue.use(Notifications); // WARNING, not used?
Vue.use(SideBar);
Vue.use(Simplert);
// global library setup
Object.defineProperty(Vue.prototype, '$Chartist', {
  get () {
    return this.$root.Chartist
  }
})
/* eslint-disable no-new */
new Vue({
  el: '#app',
  render: h => h(App),
  router,
  store,
  template: '<App/>',
  components: { App },
  data: {
    Chartist: Chartist
  }
})
