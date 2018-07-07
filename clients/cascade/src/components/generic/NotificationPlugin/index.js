import Notifications from './Notifications.vue'

const NotificationStore = {
  state: [], // here the notifications will be added

/*  removeNotification (index) {
    this.state.splice(index, 1)
  }, */
  removeNotification (timestamp) {
    console.log('Removing notification: ', timestamp)
    const indexToDelete = this.state.findIndex(n => n.timestamp === timestamp)
    if (indexToDelete !== -1) {
      this.state.splice(indexToDelete, 1)
    }
  },  
  notify (notification) {
    // Create a timestamp to serve as a unique ID for the notification.
    notification.timestamp = new Date()
    notification.timestamp.setMilliseconds(notification.timestamp.getMilliseconds() + this.state.length) 
    console.log('Adding notification: ', notification.timestamp)    
    this.state.push(notification)
  }
}

var NotificationsPlugin = {

  install (Vue) {
    Object.defineProperty(Vue.prototype, '$notifications', {
      get () {
        return NotificationStore
      }
    })
    Vue.component('Notifications', Notifications)
  }
}

export default NotificationsPlugin
