import Sidebar from './SideBar.vue'

const SidebarStore = {
  showSidebar: false,
  sidebarLinks: [
        {
          path: '/frameworks',  // CASCADE-TB DIFFERENCE
          name: 'Frameworks',
          icon: 'ti-layout',
        },
    {
      name: 'Projects',
      icon: 'ti-view-grid',
      path: '/projects'
    },
    {
      name: 'Baseline', // CASCADE-TB DIFFERENCE
      icon: 'ti-ruler-alt-2',
      path: '/calibration'
    },
    {
      name: 'Scenarios',
      icon: 'ti-control-shuffle',
      path: '/scenarios'
    },
    {
      name: 'Optimizations',
      icon: 'ti-stats-up',
      path: '/optimizations'
    },
    {
      name: 'Help',
      icon: 'ti-help',
      path: '/help'
    },
    {
      name: 'Contact',
      icon: 'ti-comment-alt',
      path: '/contact'
    },
    {
      name: 'About',
      icon: 'ti-shine',
      path: '/about'
    },
  ],

  displaySidebar (value) {
    this.showSidebar = value
  },
}

const SidebarPlugin = {

  install (Vue) {
    Vue.mixin({
      data () {
        return {
          sidebarStore: SidebarStore
        }
      }
    })

    Object.defineProperty(Vue.prototype, '$sidebar', {
      get () {
        return this.$root.sidebarStore
      }
    })
    Vue.component('side-bar', Sidebar)
  }
}

export default SidebarPlugin
