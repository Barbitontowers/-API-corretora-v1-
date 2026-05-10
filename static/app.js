let token = ""

async function login() {
    const email = document.getElementById("email").value
    const senha = document.getElementById("senha").value

    const res = await fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({email, senha})
    })

    const data = await res.json()

    token = data.token
    alert("Login realizado!")
}

async function carregarCarteira() {
    const res = await fetch("/carteira", {
        headers: {
            "Authorization": token
        }
    })

    const data = await res.json()

    document.getElementById("resultado").innerText =
        JSON.stringify(data, null, 2)
}