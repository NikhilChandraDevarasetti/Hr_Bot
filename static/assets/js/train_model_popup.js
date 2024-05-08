
var btnTrain=document.querySelector('.btn-train');
var trainModel=document.querySelector('.train-model');
var trainModelClose=document.querySelector('.train-model__header-close');
var scheduledDate=document.querySelector('#scheduled');
var now=document.querySelector('#now');
var dateContent=document.querySelector('.date-content');

btnTrain.addEventListener("click",()=>{
    trainModel.style.top="15%";
    trainModel.style.left="35%";

})
trainModelClose.addEventListener("click",()=>{
    trainModel.style.top="-420px";
})

scheduledDate.addEventListener('click',()=>{
    dateContent.style.display="block";
})
now.addEventListener("click",()=>{
        dateContent.style.display="none";
})
