<template>
  <div :class="[theme, 'message-container']">
    <transition-group name="fade" tag="div">
      <div v-for="(msg, index) in messages" :key="index" :class="['message-box', msg.type]">
        <div class="message-content">
          <span class="message-text">{{ msg.text }}</span>
          <button @click="removeMessage(index)" class="close-button" aria-label="Close message">✕</button>
        </div>
        <div class="countdown-bar" :style="{ width: (msg.timeLeft / msg.totalTime * 100) + '%' }"></div>
      </div>
    </transition-group>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'MessageBox',
  computed: {
    ...mapState(["messages", "theme"]),
  },
  methods: {
    ...mapActions(["pushMessage", "sliceMessage"]),
    startTimer(msg) {
      const interval = setInterval(() => {
        if (msg.timeLeft > 0) {
          msg.timeLeft -= 1;
        } else {
          this.removeMessage(this.messages.indexOf(msg));
          clearInterval(interval);
        }
      }, 100);
    },
    removeMessage(index) {
      this.sliceMessage(index);
    }
  },
  watch: {
    messages: {
      handler(newVal) {
        if (newVal.length > 0) {
          this.messages.forEach(msg => {
            if (!msg.intervalId) { // Only start timer if not already started
              this.startTimer(msg);
            }
          });
        }
      },
      deep: true
    }
  }
};
</script>

<style scoped>
/* Theme variables */
.light {
  --info-bg: #2196f3;
  --success-bg: #4caf50;
  --warning-bg: #ff9800;
  --error-bg: #f44336;
  --text-color: #000000;
  --countdown-bg: rgba(255, 255, 255, 0.5);
}

.dark {
  --info-bg: #1976d2;
  --success-bg: #388e3c;
  --warning-bg: #f57c00;
  --error-bg: #d32f2f;
  --text-color: #ffffff;
  --countdown-bg: rgba(255, 255, 255, 0.5);
}

.message-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  max-width: 350px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-box {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  padding: 15px 15px;
  border-radius: 6px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
  font-size: 14px;
  line-height: 1.2;
  animation: slideIn 0.3s ease-out;
}

.message-box.info {
  background-color: var(--info-bg);
}

.message-box.success {
  background-color: var(--success-bg);
}

.message-box.warning {
  background-color: var(--warning-bg);
}

.message-box.error {
  background-color: var(--error-bg);
}

.message-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.message-text {
  flex: 1;
  padding-right: 20px;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.close-button {
  background: none;
  border: none;
  color: var(--text-color);
  font-size: 1.2em;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.close-button:hover {
  transform: scale(1.2);
}

.countdown-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  background-color: var(--countdown-bg);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Slide-in animation */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>