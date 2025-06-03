<template>
    <div class="container">
        <h1>Backend Server Loading...</h1>
        <div class="loading-container">
            <div class="loading-bar"></div>
        </div>
    </div>
</template>

<style scoped>
.container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background-color: #111;
    color: white;
    text-align: center;
}

h1 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
}

.loading-container {
    width: 250px;
    height: 8px;
    background: #333;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

@keyframes loading {
    0% {
        transform: translateX(-100%);
    }

    100% {
        transform: translateX(100%);
    }
}

.loading-bar {
    width: 100%;
    height: 100%;
    background-color: #4f46e5;
    animation: loading 1.5s infinite ease-in-out;
}
</style>