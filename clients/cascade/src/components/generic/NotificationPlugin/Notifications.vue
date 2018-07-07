<!--
Definition of a Paper notification, used via this.$notifications.notify()

Last updated: 2018-03-26
-->

<template>
  <div class="notifications">
    <transition-group name="list">
      <notification v-for="(notification,index) in notifications" :key="index" :message="notification.message" :icon="notification.icon" :type="notification.type" :vertical-align="notification.verticalAlign" :horizontal-align="notification.horizontalAlign" :timeout="notification.timeout" :timestamp="notification.timestamp" @on-close="removeNotification">

      </notification>
    </transition-group>

  </div>
</template>
<script>
  import Notification from './Notification.vue'
  export default {
    components: {
      Notification
    },
    data () {
      return {
        notifications: this.$notifications.state
      }
    },
    methods: {
      removeNotification (timestamp) {
        console.log('Pre-removing notification: ', timestamp)
        this.$notifications.removeNotification(timestamp)
      }
    }
  }

</script>
<style lang="scss">
  .list-item {
    display: inline-block;
    margin-right: 10px;
  }

  .list-enter-active,
  .list-leave-active {
    transition: all 1s;
  }

  .list-enter,
  .list-leave-to
  /* .list-leave-active for <2.1.8 */

  {
    opacity: 0;
    transform: translateY(-30px);
  }
</style>
