var username
var username_span
var password
var password_span

function init(){
    username = document.getElementById("username")
    password = document.getElementById("password")

    username_span = document.createElement("span")
    password_span = document.createElement("span");

    username.parentNode.insertBefore(username_span, username)
    password.parentNode.insertBefore(password_span, password)
}

window.onload = function(e){
    init()
    var login_form = document.getElementById("login_form")
    login_form.addEventListener("submit", (evt) => {
        var valid = true;
        if(username.value == ""){
            valid = false
            username.setAttribute("class", "field-invalid")
            username_span.setAttribute("class", "error-span-invalid")
            username_span.innerText = "To pole jest wymagane"
        }
        if(password.value == ""){
            valid = false
            password.setAttribute("class", "field-invalid")
            password_span.setAttribute("class", "error-span-invalid")
            password_span.innerText = "To pole jest wymagane"
        }
        if(!valid)
            evt.preventDefault()       
    })
}