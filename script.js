document.addEventListener("DOMContentLoaded", () => {
    carregarDados();
});

async function carregarDados() {
    try {
        const res = await fetch("/api/dados");
        const data = await res.json();

        if (data.has_file) {
            renderizarTabela(data.colunas, data.dados);
            document.getElementById("btn-download").style.display = "inline-block";
        }
    } catch (err) {
        exibirFeedback("Erro ao carregar dados.", false);
    }
}

async function enviarPlanilha(e) {
    e.preventDefault();
    const fileInput = document.getElementById("excel-file");
    if (fileInput.files.length === 0) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (res.ok) {
        exibirFeedback(data.message, true);
        carregarDados();
        fileInput.value = "";
    } else {
        exibirFeedback(data.message, false);
    }
}

async function biparItem(e) {
    e.preventDefault();
    const input = document.getElementById("codigo-input");
    const codigo = input.value.trim();

    if (!codigo) return;

    try {
        const res = await fetch("/api/incrementar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ codigo })
        });

        const data = await res.json();

        if (res.ok) {
            exibirFeedback(data.message, true);
            
            // Exibe o Card de Resultado com Coluna D e Coluna G
            document.getElementById("card-resultado").style.display = "block";
            document.getElementById("res-codigo").textContent = data.codigo;
            document.getElementById("res-qtd").textContent = data.qtd_contada;
            
            document.getElementById("label-col-d").textContent = data.coluna_d.nome;
            document.getElementById("val-col-d").textContent = data.coluna_d.valor;

            document.getElementById("label-col-g").textContent = data.coluna_g.nome;
            document.getElementById("val-col-g").textContent = data.coluna_g.valor;

            input.value = "";
            input.focus();
            carregarDados();
        } else {
            exibirFeedback(data.message, false);
            input.select();
        }
    } catch (err) {
        exibirFeedback("Erro ao processar o código.", false);
    }
}

function renderizarTabela(colunas, dados) {
    const cabecalho = document.getElementById("cabecalho-tabela");
    const corpo = document.getElementById("corpo-tabela");

    cabecalho.innerHTML = "";
    corpo.innerHTML = "";

    colunas.forEach(col => {
        const th = document.createElement("th");
        th.textContent = col;
        cabecalho.appendChild(th);
    });

    dados.forEach(linha => {
        const tr = document.createElement("tr");
        colunas.forEach(col => {
            const td = document.createElement("td");
            td.textContent = linha[col];
            tr.appendChild(td);
        });
        corpo.appendChild(tr);
    });
}

function exibirFeedback(mensagem, sucesso) {
    const box = document.getElementById("feedback");
    box.textContent = mensagem;
    box.className = `feedback ${sucesso ? 'sucesso' : 'erro'}`;
    box.style.display = "block";

    setTimeout(() => { box.style.display = "none"; }, 3000);
}