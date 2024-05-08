const logoutModal = document.getElementById('logoutmodal');
const imageBox = document.getElementById('imagebox');
const helpModal = document.getElementById('helpmodal');
const helpBox = document.getElementById('helpbox');


imageBox.addEventListener("click", () => {
    if (logoutModal.style.display == "none") {
        logoutModal.style.display = "block";
        helpModal.style.display = "none"
    } else {
        logoutModal.style.display = "none";
    }
})
helpBox.addEventListener("click", () => {
    if (helpModal.style.display == "none") {
        helpModal.style.display = "block";
        logoutModal.style.display = "none";
    } else {
        helpModal.style.display = "none";
    }
})

window.onclick = function (event) {
    if (event.target.matches(".userimage")==false) {
        logoutModal.style.display = "none";
    } 
    if (event.target.matches(".helpimage")==false) {
        helpModal.style.display = "none";
    } 
}



