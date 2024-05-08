/* toggle button code */
var toggle_btn= document.getElementById('toggle');
var sidenav= document.getElementById('sidenav');
var logo= document.getElementById('logo');
var content= document.getElementById('content');

toggle_btn.addEventListener('click', function(){
    if(toggle_btn.classList.contains('close')){
        sidenav.style.width= '240px';
        sidenav.style.paddingLeft= '34px';

        content.style.width= 'calc(100% - 240px)';

        logo.classList.add('d-flex');

        toggle_btn.classList.remove('close');
        toggle_btn.classList.add('open');

        sidenav.classList.add('open');
        sidenav.classList.remove('close');
    }else{
        logo.classList.remove('d-flex');
        logo.style.display= 'none';

        sidenav.style.width= '145px';
        sidenav.style.paddingLeft= '15px';

        content.style.width = 'calc(100% - 145px)';

        toggle_btn.classList.remove('open');
        toggle_btn.classList.add('close');

        sidenav.classList.remove('open');
        sidenav.classList.add('close');
    }
});
/* toggle button code end */

/* action button code start */
var actionPopup;
var actionBtn;

function handleMenuClick(e){
    actionBtn = e;
    actionPopup = e.nextElementSibling;
    if(actionPopup.classList.contains('open')){
        actionPopup.classList.remove('open');
        actionPopup.classList.add('close');
    }else{
        actionPopup.classList.remove('close');
        actionPopup.classList.add('open');
    }
}

window.onclick = function(event){
    if (event.target != actionPopup && event.target != actionBtn) {
        actionPopup.classList.remove('open');
        actionPopup.classList.add('close');
    }
}

/* edit popup code start */
var editPopup;
var editBtn;

var deletePopup;
var deleteBtn;

var edit_pop = document.getElementById('EditPopup');
var blurElement = document.getElementById('blur-bg');
var delete_pop = document.getElementById('DeletePopup');

function editBtnClick(val){
    editBtn= val;
    editPopup = val.nextElementSibling;
    edit_pop.style.display = 'block';
    blurElement.style.display = 'block';
}
function deleteBtnClick(del_val){
    deleteBtn= del_val;
    deletePopup = del_val.nextElementSibling;
    delete_pop.style.display = 'block';
    blurElement.style.display = 'block';
}
blurElement.addEventListener('click', function(){
    edit_pop.style.display = 'none';
    delete_pop.style.display = 'none';
    blurElement.style.display = 'none';
});
/* action btn code end */

function openMenu(){
    const openIcon=document.getElementById('open-menu');
    const closeIcon=document.getElementById('close-menu');
    sidenav.style.left="0px";
    sidenav.style.transition="left 0.5s linear";
    // openIcon.style.display="none";
    closeIcon.style.display="block";
    // openIcon.style.display="none";
    toggle_btn.style.display="none";
}
function closeMenu(){
    const openIcon=document.getElementById('open-menu');
    const closeIcon=document.getElementById('close-menu');
    sidenav.style.left="-300px";
    sidenav.style.transition="left 0.5s linear";
    closeIcon.style.display="none";
    // openIcon.style.display="block";
}