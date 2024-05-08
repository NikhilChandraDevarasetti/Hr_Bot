/* Count details popup code start */
var blurElement = document.getElementById('blur-bg');
var countDPopup = document.getElementById('countDetailsPopup');
var closeCountDetailsPopup=document.querySelector('.countDetailsPopup__close');



function countDetails(){
    countDPopup.style.display = 'block';
    blurElement.style.display = 'block';
}
blurElement.addEventListener('click', function(){
    countDPopup.style.display = 'none';
    blurElement.style.display = 'none';
});
closeCountDetailsPopup.addEventListener('click', function(){
    countDPopup.style.display = 'none';
    blurElement.style.display = 'none';
});


