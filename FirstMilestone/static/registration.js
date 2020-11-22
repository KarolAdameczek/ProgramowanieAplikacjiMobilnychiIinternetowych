const login_regex = /^[a-z]{3,12}$/
const name_regex = /^[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+$/
const password_regex = /^.{8,}$/
const login_availability_url = "https://infinite-hamlet-29399.herokuapp.com/check/"
const input_ids = ["login", "firstname", "lastname", "password", "repeated_password", "sex", "photo"]

window.onload = function(e){
    setupInputRealTimeValidation()
    setupSubmit()
}

function setupSubmit(){
    var register_form = document.getElementById("register_form")
    register_form.addEventListener("submit", (evt) => {
        var valid = true
        for( var input_id of input_ids ){
            input = document.getElementById(input_id)
            if( !input.checkValidity() || !input.value ){
                input.setCustomValidity("To pole jest wymagane")
                input.reportValidity()
                valid = false;
            }
        }
        if(!valid)
            evt.preventDefault()
    })
}

function setupInputRealTimeValidation(){
    var login_input = document.getElementById("login")
    var firstname_input = document.getElementById("firstname")
    var lastname_input = document.getElementById("lastname")
    var password_input = document.getElementById("password")
    var repeated_password_input = document.getElementById("repeated_password")
    var photo_input = document.getElementById("photo")

    login_input.addEventListener("change", function(e) {
        if(!login_input.value.match(login_regex)) {
            login_input.setCustomValidity("Nazwa użytkownika musi składać się z od 3 do 8 małych liter łacińskich.")
            login_input.reportValidity()
        }
    })

    login_input.addEventListener("input", function(e) {
        login_input.setCustomValidity("")
        if(login_input.value.match(login_regex)){
            var xhr = new XMLHttpRequest()
            xhr.open("GET", login_availability_url + login_input.value)
            xhr.responseType = "json"
            xhr.onload = function() {
                console.info()
                if(xhr.status >= 200 && xhr.status < 300){
                    if(xhr.response[login_input.value] == "taken"){
                        login_input.setCustomValidity("Nazwa użytkownika jest zajęta")
                    }
                    else if(xhr.response[login_input.value] == "available"){
                        login_input.setCustomValidity("")
                    }
                    login_input.reportValidity()                 
                } else if (xhr.status >= 400 && xhr.status < 500) {
                    login_input.setCustomValidity("Wystąpił błąd aplikacji, prosimy skontaktować się z administratorem")
                } else if (xhr.status >= 500 && xhr.status < 600) {
                    login_input.setCustomValidity("Wystąpił błąd serwera, prosimy spróbować ponownie później")
                } else {
                    console.error("Unexpected result while checking login availability, response code: ", xhr.status )
                }
            }
            xhr.send();
        }
    })

    password_input.addEventListener("change", function(e) {
        if(password_input.value.match(password_regex)){
            password_input.setCustomValidity("")
        } else {
            password_input.setCustomValidity("Hasło musi składać się z conajmniej 8 znaków")
            password_input.reportValidity()
        }
        var event = new Event('input', {
            bubbles: true,
            cancelable: true,
        });
        repeated_password_input.dispatchEvent(event);
    })

    password_input.addEventListener("input", function(e) {
        password_input.setCustomValidity("")
        password_input.reportValidity()
    })

    repeated_password_input.addEventListener("change", function(e) {
        if(repeated_password_input.value == password_input.value){
            repeated_password_input.setCustomValidity("")
        } else {
            repeated_password_input.setCustomValidity("Hasła nie są identyczne")
            repeated_password_input.reportValidity()
        }
    })

    repeated_password_input.addEventListener("input", function(e) {
        repeated_password_input.setCustomValidity("")
        repeated_password_input.reportValidity()
    })

    const simpleRegexCheck = function(input, regex, message){
        input.addEventListener("change", function(e) {
            if(!input.value.match(regex)) {
                input.setCustomValidity(message)
                input.reportValidity()
            }
        })
        input.addEventListener("input", function(e) {
            input.setCustomValidity("")
            input.reportValidity()
        })

    }

    simpleRegexCheck(firstname_input, name_regex, "Imię musi zaczynać się od wielkiej litery i mieć co najmniej dwie litery długości")
    simpleRegexCheck(lastname_input, name_regex, "Nazwisko musi zaczynać się od wielkiej litery i mieć co najmniej dwie litery długości")

    photo_input.addEventListener("change", function (e) {
        if(!photo_input.value.endsWith(".jpg") && !photo_input.value.endsWith(".png")) {
            photo_input.value = null
            photo_input.setCustomValidity("Dozwolone są tylko pliki w formacie .jpg lub .png")
            photo_input.reportValidity()
        }
    })
}

