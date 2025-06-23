<template>
    <video class="BackgroundVideo" autoplay muted loop>
        <source src="../assets/BackGround.mp4" type="video/mp4" />
        Your browser does not support HTML5 video.
    </video>
    <div class="loginDiv">
        <div class="loginPanel">
            <div class="panel-body">
                <fieldset>
                    <legend class="panel-title">Sign in to CWA Viewer</legend>
                    <form @submit.prevent="login(false)">
                        <div class="formGroup">
                            <label for="username"><b>Email address:</b></label>
                            <input id="username" type="text" v-model="username" class="formControl" maxlength="50"
                                required autocomplete="username" />
                        </div>
                        <div class="formGroup">
                            <label for="password"><b>Password:</b></label>
                            <div class="passwordWrapper">
                                <input id="password" :type="showPassword ? 'text' : 'password'" v-model="password"
                                    class="formControl" maxlength="50" required autocomplete="current-password" />
                                <span class="togglePassword" @click="togglePasswordVisibility">
                                    <svg v-if="showPassword" xmlns="http://www.w3.org/2000/svg" class="eyeIcon"
                                        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                        stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                        <circle cx="12" cy="12" r="3"></circle>
                                    </svg>
                                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="eyeIcon" viewBox="0 0 24 24"
                                        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                        stroke-linejoin="round">
                                        <path d="M2 12s4-5 10-5 10 5 10 5-4 5-10 5-10-5-10-5z"></path>
                                        <path d="M4 18l1-2"></path>
                                        <path d="M8 20l1-2"></path>
                                        <path d="M16 20l-1-2"></path>
                                        <path d="M20 18l-1-2"></path>
                                    </svg>
                                </span>
                            </div>
                        </div>
                        <HCaptcha :sitekey="sitekey" :reCaptchaCompat="false" @verify="onHCaptchaChange" />
                        <button type="submit" class="loginButton">Sign in</button>
                        <button type="button" class="contactAdminButton" @click="showContactForm = true">Contact
                            Admin</button>
                        <button type="button" class="helpButton" @click="showHelpPopup = true">Help</button>
                        <p v-if="error" class="errorMessage">{{ error }}</p>
                    </form>
                </fieldset>
            </div>
        </div>
    </div>
    <div v-if="showContactForm" class="contactFormOverlay">
        <div class="contactForm">
            <h3>Contact Admin</h3>
            <form :action="formSubmitUrl" method="POST">
                <div class="formGroup">
                    <label for="name"><b>Name:</b></label>
                    <input id="name" name="name" type="text" placeholder="Full Name" class="formControl" required />
                </div>
                <div class="formGroup">
                    <label for="email"><b>Email:</b></label>
                    <input id="email" name="email" type="email" placeholder="Email Address" class="formControl"
                        required />
                </div>
                <div class="formGroup">
                    <label for="message"><b>Message:</b></label>
                    <textarea id="message" name="message" placeholder="Your Message" class="formControl" rows="4"
                        required></textarea>
                </div>
                <input type="hidden" name="_cc" :value="cc" />
                <input type="hidden" name="_next" :value="thankYouUrl">
                <input type="hidden" name="_subject" value="Contact from CWA Viewer Form">
                <input type="hidden" name="_template" value="box">
                <button type="submit" class="submitButton">Send</button>
                <button type="button" class="cancelButton" @click="showContactForm = false">Cancel</button>
            </form>
        </div>
    </div>
    <div v-if="showHelpPopup" class="contactFormOverlay">
        <div class="helpPopup">
            <h3>Help</h3>
            <p>If you are having trouble with the website, contact admin or use the desktop app with the same
                functionality and features as the web app.</p>
            <p>
                <a href="https://github.com/shahviransh/ECCC-IMWEBs-Viewer?tab=readme-ov-file#-installation"
                    target="_blank">
                    Click here and follow installation instructions.
                </a>
            </p>
            <button type="button" class="cancelButton" @click="showHelpPopup = false">Close</button>
        </div>
    </div>
    <div class="logos">
        <img src="../assets/ECCC.png" alt="ECCC Logo" class="ecccLogo" />
        <img src="../assets/CWA.png" alt="CWA Logo" class="cwaLogo" />
    </div>
</template>

<script>
import axios from 'axios';
import HCaptcha from '@hcaptcha/vue3-hcaptcha';

export default {
    data() {
        return {
            username: '',
            password: '',
            error: '',
            showPassword: false,
            showContactForm: false,
            captchaToken: null,
            formSubmitUrl: `https://formsubmit.co/${import.meta.env.VITE_FORM_SUBMIT_ID}`,
            sitekey: import.meta.env.VITE_HCAPTCHA_SITE_KEY,
            cc: import.meta.env.VITE_RECIPIENTS,
            thankYouUrl: `${import.meta.env.VITE_API_BASE_URL}/thank-you.html`,
            showHelpPopup: false
        };
    },
    props: {
        isAuthenticated: Boolean
    },
    components: {
        HCaptcha
    },
    methods: {
        togglePasswordVisibility() {
            this.showPassword = !this.showPassword;
        },
        async login(autoLogin) {
            try {
                const credentials = autoLogin
                    ? { username: 'default', password: 'default' }
                    : { username: this.username, password: this.password };

                if (!autoLogin && !this.captchaToken) {
                    this.error = 'Please complete the CAPTCHA';
                    return;
                }

                const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/login`, credentials);
                const token = response.data.access_token;
                localStorage.setItem('token', token);
                this.$emit("update:isAuthenticated", true);
            } catch (err) {
                console.error(err);
                this.error = err.response?.data?.error || 'Invalid username or password';
            }
        },
        onHCaptchaChange(captchaToken) {
            this.captchaToken = captchaToken;
        },
    },
    mounted() {
        // Auto login in Tauri
        if (window.__TAURI__) {
            this.login(true);
        }
    }
};
</script>

<style scoped>
html,
body {
    position: relative;
    min-height: 100vh;
    margin: 0;
}

.loginDiv {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    padding: 20px;
}

.BackgroundVideo {
    position: fixed;
    right: 0;
    bottom: 0;
    min-width: 100%;
    min-height: 100%;
    opacity: 0.8;
    z-index: -1;
}

.loginPanel {
    text-align: center;
}

.site-logo {
    margin: 20px 0;
}

.panel-title {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 20px;
    color: #333;
}

.formGroup {
    margin-bottom: 10px;
    text-align: left;
}

.formGroup label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #555;
}

.formControl {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
    box-sizing: border-box;
}

.formControl:focus {
    border-color: #007bff;
    outline: none;
    box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
}

.loginButton {
    width: 100%;
    padding: 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    margin-top: 10px;
    transition: background-color 0.3s ease;
}

.loginButton:hover {
    background-color: #0056b3;
    transform: translateY(-2px);
}

.errorMessage {
    color: red;
    margin-top: 10px;
    font-size: 0.9rem;
    text-align: left;
}

.passwordWrapper {
    position: relative;
    display: flex;
    align-items: center;
}

.passwordWrapper .formControl {
    flex: 1;
}

.togglePassword {
    position: absolute;
    cursor: pointer;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #007bff;
}

.togglePassword:hover {
    color: #0056b3;
}

.eyeIcon {
    width: 20px;
    height: 20px;
}

.contactAdminButton {
    width: 100%;
    padding: 10px;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.contactAdminButton:hover {
    background-color: #218838;
}

.contactFormOverlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.contactForm {
    background: white;
    padding: 20px;
    border-radius: 8px;
    width: 400px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.contactForm h3 {
    text-align: center;
}

.submitButton {
    width: 100%;
    padding: 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.submitButton:hover {
    background-color: #0056b3;
}

.cancelButton {
    width: 100%;
    padding: 10px;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.cancelButton:hover {
    background-color: #c82333;
}

.helpButton {
    width: 100%;
    padding: 10px;
    background-color: #ffc107;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.helpButton:hover {
    background-color: #e0a800;
}

.helpPopup {
    background: white;
    padding: 10px;
    border-radius: 8px;
    width: 400px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    text-align: center;
}

.helpPopup h3 {
    text-align: center;
}

.helpPopup p {
    font-size: 1rem;
    color: #333;
}

.helpPopup a {
    color: #007bff;
    text-decoration: none;
}

.helpPopup a:hover {
    text-decoration: underline;
}

.logos {
    position: fixed;
    bottom: 10px;
    right: 10px;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    z-index: 1000;
}

.ecccLogo,
.cwaLogo {
    width: 250px;
    margin-bottom: 10px;
}

.cwaLogo {
    margin-bottom: 0;
}
</style>