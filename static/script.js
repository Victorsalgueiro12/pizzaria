document.addEventListener("DOMContentLoaded", function () {

let carrinho = JSON.parse(localStorage.getItem("carrinho")) || []

const cartCount = document.getElementById("cartCount")
const cartModal = document.getElementById("cartModal")
const cartButton = document.getElementById("cartButton")
const closeCart = document.getElementById("closeCart")
const cartItems = document.getElementById("cartItems")
const cartTotal = document.getElementById("cartTotal")

/* ============================ */
/* FUNÇÕES BASE */
/* ============================ */

function salvarCarrinho() {
    localStorage.setItem("carrinho", JSON.stringify(carrinho))
}

function atualizarContador() {
    const totalItens = carrinho.reduce((total, item) => total + item.quantidade, 0)
    cartCount.innerText = totalItens
}

function atualizarCarrinhoUI() {
    cartItems.innerHTML = ""
    let total = 0

    carrinho.forEach((item, index) => {

        total += item.preco * item.quantidade

        cartItems.innerHTML += `
        <div class="flex justify-between items-center bg-black/40 p-2 rounded-lg text-sm">

            <div>
                <p class="font-semibold text-sm">${item.nome}</p>
                <p class="text-xs text-gray-400">
                    ${item.quantidade}x • R$ ${(item.preco * item.quantidade).toFixed(2)}
                </p>
            </div>

            <div class="flex items-center gap-1">

                <button onclick="diminuirQuantidade(${index})"
                class="bg-gray-700 px-2 rounded text-xs">-</button>

                <span class="text-sm">${item.quantidade}</span>

                <button onclick="aumentarQuantidade(${index})"
                class="bg-gray-700 px-2 rounded text-xs">+</button>

                <button onclick="removerItem(${index})"
                class="text-red-500 font-bold ml-2 text-sm">
                ✕
                </button>

            </div>

        </div>
        `
    })

    cartTotal.innerText = `R$ ${total.toFixed(2)}`
}

/* ============================ */
/* FUNÇÕES CARRINHO */
/* ============================ */

window.adicionarAoCarrinho = function (id, nome, preco) {

    const itemExistente = carrinho.find(item => item.id === id)

    if (itemExistente) {
        itemExistente.quantidade += 1
    } else {
        carrinho.push({
            id: id,
            nome: nome,
            preco: Number(preco),
            quantidade: 1
        })
    }

    salvarCarrinho()
    atualizarContador()
    atualizarCarrinhoUI()
}

window.removerItem = function (index) {
    carrinho.splice(index, 1)
    salvarCarrinho()
    atualizarContador()
    atualizarCarrinhoUI()
}

window.aumentarQuantidade = function (index) {
    carrinho[index].quantidade += 1
    salvarCarrinho()
    atualizarContador()
    atualizarCarrinhoUI()
}

window.diminuirQuantidade = function (index) {
    if (carrinho[index].quantidade > 1) {
        carrinho[index].quantidade -= 1
    } else {
        carrinho.splice(index, 1)
    }

    salvarCarrinho()
    atualizarContador()
    atualizarCarrinhoUI()
}

/* ============================ */
/* ABRIR / FECHAR MODAL */
/* ============================ */

if (cartButton) {
    cartButton.addEventListener("click", () => {
        cartModal.classList.remove("hidden")
    })
}

if (closeCart) {
    closeCart.addEventListener("click", () => {
        cartModal.classList.add("hidden")
    })
}

/* ============================ */
/* CARREGAR PRODUTOS - LISTA PROFISSIONAL */
/* ============================ */

fetch("/produtos")
.then(res => res.json())
.then(data => {

    const container = document.getElementById("produtos")
    const categorias = {}

    data.forEach(produto => {
        if (!categorias[produto.categoria]) {
            categorias[produto.categoria] = []
        }
        categorias[produto.categoria].push(produto)
    })

    for (let categoria in categorias) {

        container.innerHTML += `
        <h2 class="text-lg sm:text-xl font-bold mt-8 mb-4">
        ${categoria}
        </h2>

        <div class="space-y-4">
        ${categorias[categoria].map(p => `
        <div class="flex gap-3 items-center bg-black/30 p-3 rounded-xl hover:bg-black/50 transition">

            <!-- IMAGEM -->
            <img src="/static/uploads/${p.imagem}" 
            class="w-20 h-20 sm:w-24 sm:h-24 object-cover rounded-lg">

            <!-- INFO -->
            <div class="flex-1">

                <h3 class="text-sm sm:text-base font-semibold">
                ${p.nome}
                </h3>

                <p class="text-gray-400 text-xs mt-1 line-clamp-2">
                ${p.descricao || ""}
                </p>

                <div class="flex justify-between items-center mt-2">

                    <span class="text-red-500 font-bold text-sm sm:text-base">
                    R$ ${Number(p.preco).toFixed(2)}
                    </span>

                    <button onclick="adicionarAoCarrinho(${p.id}, '${p.nome}', ${p.preco})"
                    class="bg-red-500 hover:bg-red-600 transition px-3 py-1.5 rounded-lg text-xs font-semibold">
                    + Adicionar
                    </button>

                </div>

            </div>

        </div>
        `).join("")}
        </div>
        `
    }

    atualizarContador()
    atualizarCarrinhoUI()
})

/* ============================ */
/* FINALIZAR PEDIDO */
/* ============================ */

window.finalizarPedido = async function () {

    if (carrinho.length === 0) {
        alert("Seu carrinho está vazio!")
        return
    }

    const endereco = document.getElementById("endereco").value
    const pagamento = document.getElementById("pagamento").value
    const observacao = document.getElementById("observacao").value

    if (!endereco || !pagamento) {
        alert("Preencha endereço e forma de pagamento!")
        return
    }

    let total = 0

    carrinho.forEach(item => {
        total += item.preco * item.quantidade
    })

    const dados = {
        endereco: endereco,
        pagamento: pagamento,
        observacao: observacao,
        total: total,
        itens: carrinho
    }

    try {

        await fetch("/finalizar_pedido", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(dados)
        })

        let mensagem = "🍕 *NOVO PEDIDO*\n\n"

        carrinho.forEach(item => {
            mensagem += `• ${item.quantidade}x ${item.nome} - R$ ${(item.preco * item.quantidade).toFixed(2)}\n`
        })

        mensagem += `\n💰 *Total:* R$ ${total.toFixed(2)}\n`
        mensagem += `📍 *Endereço:* ${endereco}\n`
        mensagem += `💳 *Pagamento:* ${pagamento}\n`

        if (observacao) {
            mensagem += `📝 *Observação:* ${observacao}\n`
        }

        const telefone = "82999607423"
        const mensagemFormatada = encodeURIComponent(mensagem)

        window.open(`https://wa.me/${telefone}?text=${mensagemFormatada}`, "_blank")

        carrinho = []
        salvarCarrinho()
        atualizarContador()
        atualizarCarrinhoUI()

        alert("Pedido enviado com sucesso!")

    } catch (error) {
        alert("Erro ao enviar pedido.")
        console.error(error)
    }
}

})