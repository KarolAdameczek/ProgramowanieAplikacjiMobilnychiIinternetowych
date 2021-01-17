const person_regex = /[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+ [A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+/
var person
var person_span
var person_valid
var socket

function init(){
    person = document.getElementById("person")
    person_span = document.createElement("span");

    if(person) { person.addEventListener("change", check_person) }

    person.parentNode.insertBefore(person_span, person)
}

function check_person(){
    if(person.value.match(person_regex)){
        person.setAttribute("class", "field-valid")
        person_span.setAttribute("class", "error-span-hidden")
        person_span.innerText = ""
        person_valid = true
    } else {
        person.setAttribute("class", "field-invalid")
        person_span.setAttribute("class", "error-span-invalid")
        person_span.innerText = "Należy podać imię i nazwisko zaczynające się od wielkich liter oddzielone spacją"
        person_valid = false
    }
}

window.onload = function(e){
    init()
    var label_form = document.getElementById("label_form")
    label_form.addEventListener("submit", (evt) => {
        var valid = true;
        if(person.value == "" || !person_valid){
            valid = false
            person.setAttribute("class", "field-invalid")
            person_span.setAttribute("class", "error-span-invalid")
            person_span.innerText = "Należy podać imię i nazwisko zaczynające się od wielkich liter oddzielone spacją"
        }
        if(!valid)
            evt.preventDefault()       
    })
    
    if(typeof token !== 'undefined' && typeof socket_url !== 'undefined' ){
        socket = io(socket_url);
        socket.emit("login", {token : token});

        h2 = document.getElementsByTagName("h2")[0]
        ul = document.createElement("ul")
        ul.id = "notifications"
        h2.parentNode.insertBefore(ul, h2)

        socket.on('message', function(data) {
            if(data.hasOwnProperty("notification")){
                var flashesUl = document.getElementById("notifications");
                var li = document.createElement("li");
                li.className = "notification";
                li.innerText = data["notification"];
                flashesUl.appendChild(li);
            };
        });
    }
}