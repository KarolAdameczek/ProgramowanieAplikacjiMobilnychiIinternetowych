const login_availability_url = "/sender/checkusername/"
var error_spans = {}
var error_message = {}
var form_fields = {}
var field_validation = {}
var field_regexes = {}
var form

window.onload = function(e){
    init()
    setupSubmit()
}

function init(){
    form = document.forms[0]
    var firstname = document.getElementById("firstname")
    var lastname  = document.getElementById("lastname")
    var username  = document.getElementById("username")
    var email     = document.getElementById("email")
    var address   = document.getElementById("address")
    var password  = document.getElementById("password")
    var password2 = document.getElementById("password2")
    
    form_fields["firstname"] = firstname
    form_fields["lastname"]  = lastname 
    form_fields["username"]  = username
    form_fields["email"]     = email
    form_fields["address"]   = address
    form_fields["password"]  = password
    form_fields["password2"] = password2

    field_regexes["firstname"] = /^[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+$/
    field_regexes["lastname"]  = /^[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+$/
    field_regexes["username"]  = /^[a-z]{3,12}$/
    field_regexes["email"]     = /^(([^<>()\[\]\.,;:\s@\"]+(\.[^<>()\[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/
    field_regexes["address"]   = /^[A-ZŻŹĆĄŚĘŁÓŃa-zżźćńółęąś. 0-9]{8,100}$/
    field_regexes["password"]  = /^.{8,}$/

    error_message["firstname"]       = "Imię musi zaczynać się od wielkiej litery i mieć co najmniej dwie litery długości"
    error_message["lastname"]        = "Nazwisko musi zaczynać się od wielkiej litery i mieć co najmniej dwie litery długości"
    error_message["username"]        = "Nazwa użytkownika musi składać się z od 3 do 8 małych liter łacińskich."
    error_message["username-taken"]  = "Nazwa użytkownika jest zajęta"
    error_message["email"]           = "Niepoprawny format adresu email"
    error_message["address"]         = "Adres jest za krótki lub zawiera niedozwolone znaki"
    error_message["password"]        = "Hasło musi składać się z conajmniej 8 znaków"
    error_message["password2"]       = "Hasła nie są identyczne"

    for(var name in form_fields){
        error_spans[name] = document.createElement("span");
        form_fields[name].parentNode.insertBefore(error_spans[name], form_fields[name])
    }

    if(username)  { username.addEventListener("input", check_username)}
    if(firstname) { firstname.addEventListener("change", function() {check_with_regex("firstname")})}
    if(lastname)  { lastname.addEventListener("change", function() {check_with_regex("lastname")})}
    if(email)     { email.addEventListener("change", function() {check_with_regex("email")})}
    if(address)   { address.addEventListener("change", function() {check_with_regex("address")})}
    if(password)  { password.addEventListener("change", check_password)}
    if(password2) { password2.addEventListener("change", check_password2)}
}

function check_with_regex(name){
    if(form_fields[name].value.match(field_regexes[name])){
        form_fields[name].setAttribute("class", "field-valid")
        error_spans[name].setAttribute("class", "error-span-hidden")
        error_spans[name].innerText = ""
        field_validation[name] = true
    } else {
        form_fields[name].setAttribute("class", "field-invalid")
        error_spans[name].setAttribute("class", "error-span-invalid")
        error_spans[name].innerText = error_message[name]
        field_validation[name] = false
    }
}

function check_username(){
    if(form_fields["username"].value.match(field_regexes["username"])){
        var xhr = new XMLHttpRequest()
        var username = form_fields["username"].value
        xhr.open("GET", login_availability_url + username)
        xhr.responseType = "json"
        xhr.onload = function() {
            if(xhr.status >= 200 && xhr.status < 300){
                if(xhr.response[username] == "taken"){
                    form_fields["username"].setAttribute("class", "field-invalid")
                    error_spans["username"].setAttribute("class", "error-span-invalid")
                    error_spans["username"].innerText = error_message["username-taken"]
                    field_validation["username"] = false
                }
                else if(xhr.response[username] == "available"){
                    form_fields["username"].setAttribute("class", "field-valid")
                    error_spans["username"].setAttribute("class", "error-span-hidden")
                    error_spans["username"].innerText = ""
                    field_validation["username"] = true
                }
            }
        }
        xhr.send();
    } else {
        form_fields["username"].setAttribute("class", "field-invalid")
        error_spans["username"].setAttribute("class", "error-span-invalid")
        error_spans["username"].innerText = error_message["username"]
        field_validation["username"] = false
    }
}

function check_password(){
    if(form_fields["password"].value.match(field_regexes["password"])){
        form_fields["password"].setAttribute("class", "field-valid")
        error_spans["password"].setAttribute("class", "error-span-hidden")
        error_spans["password"].innerText = ""
        field_validation["password"] = true
        if(form_fields["password2"].value != ""){
            check_password2()
        }
    } else {
        form_fields["password"].setAttribute("class", "field-invalid")
        error_spans["password"].setAttribute("class", "error-span-invalid")
        error_spans["password"].innerText = error_message["password"]
        field_validation["password"] = false
    }
}

function check_password2(){
    if(form_fields["password"].value == form_fields["password2"].value){
        form_fields["password2"].setAttribute("class", "field-valid")
        error_spans["password2"].setAttribute("class", "error-span-hidden")
        error_spans["password2"].innerText = ""
        field_validation["password2"] = true
    } else {
        form_fields["password2"].setAttribute("class", "field-invalid")
        error_spans["password2"].setAttribute("class", "error-span-invalid")
        error_spans["password2"].innerText = error_message["password2"]
        field_validation["password2"] = false
    }
}

function setupSubmit(){
    var register_form = document.getElementById("register_form")
    register_form.addEventListener("submit", (evt) => {
        var valid = true
        for(var name in form_fields){
            if(form_fields[name].value == "" || !field_validation[name]){
                valid = false
                form_fields[name].setAttribute("class", "field-invalid")
                error_spans[name].setAttribute("class", "error-span-invalid")
                error_spans[name].innerText = "To pole jest wymagane"
                field_validation[name] = false
            }
        }
        if(!valid)
            evt.preventDefault()
    })
}