const person_regex = /[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+ [A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+/
var person
var person_span
var person_valid


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
}