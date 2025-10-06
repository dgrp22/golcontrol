// ---------- referencias UI ----------
const monthYear   = document.getElementById("monthYear");
const calendar    = document.getElementById("calendar");
const modal       = document.getElementById("modal");
const closeModal  = document.getElementById("closeModal");
const selectedDay = document.getElementById("selectedDay");
const hoursGrid   = document.getElementById("hoursGrid");

// Modal de reserva
const reserveModal      = document.getElementById("reserveModal");
const closeReserveModal = document.getElementById("closeReserveModal");
const reserveForm       = document.getElementById("reserveForm");
const selectedHourText  = document.getElementById("selectedHour");

// Campo duración y costo
const duracionSelect = document.getElementById("duracion");
const costoInput     = document.getElementById("costo");

// Historial del día
const viewDayHistory   = document.getElementById("viewDayHistory");
const dayHistoryModal  = document.getElementById("dayHistoryModal");
const closeDayHistory  = document.getElementById("closeDayHistory");
const dayHistoryTitle  = document.getElementById("dayHistoryTitle");
const dayHistoryContent= document.getElementById("dayHistoryContent");

// Tabs de canchas
const tabButtons = document.querySelectorAll(".tab-btn");

// ---------- estado ----------
const today = new Date();
let currentMonth = today.getMonth();
let currentYear  = today.getFullYear();

// Estructura: reservas[fecha][cancha][hora] = { ... }
const reservas = Object.create(null);

let lastDay = null, lastMonth = null, lastYear = null;
let selectedHour = null;
let activeCancha = "C1"; // por defecto

// ---------- helpers ----------
const pad = n => String(n).padStart(2,"0");
const dateKey = (y,m,d) => `${y}-${pad(m+1)}-${pad(d)}`; 
const costoHora = h => (h < 18 ? 60 : 100);
const rangoTexto = (start, dur) => `${pad(start)}:00–${pad(start + dur)}:00`;

function estadoTexto(e) {
  if (e === "noabono") return "Reservado sin abono";
  if (e === "partial") return "Parcial";
  if (e === "reserved") return "Pagado";
  return "Libre";
}

// ---------- render calendario ----------
function renderCalendar(month, year) {
  monthYear.textContent = new Date(year, month).toLocaleString("es-ES", {
    month: "long", year: "numeric"
  });

  calendar.innerHTML = "";

  const firstDay = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();
  const start = (firstDay + 6) % 7;

  for (let i = 0; i < start; i++) {
    const empty = document.createElement("div");
    empty.classList.add("day-card", "empty");
    calendar.appendChild(empty);
  }

  for (let d = 1; d <= lastDate; d++) {
    const card = document.createElement("div");
    card.classList.add("day-card");
    card.textContent = d;

    if (d === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
      card.style.background = "var(--gold)";
      card.style.color = "#000";
      card.style.fontWeight = "bold";
    }

    card.onclick = () => openModal(d, month, year);
    calendar.appendChild(card);
  }
}

// ---------- abrir modal de horarios ----------
async function openModal(day, month, year) {
  lastDay = day; lastMonth = month; lastYear = year;
  selectedDay.textContent = `Horarios ${day}/${month + 1}/${year}`;

  const fecha = dateKey(year, month, day);
  const cancha_id = activeCancha === "C1" ? 1 : activeCancha === "C2" ? 2 : 3;

  try {
    const res = await fetch(`https://golcontrol-g7gkhdbbg2hbgma8.canadacentral-01.azurewebsites.net/reservas?fecha=${fecha}&cancha_id=${cancha_id}`);
    const data = await res.json();
    if (data.ok) {
      reservas[fecha] = {};
      reservas[fecha][activeCancha] = {};

      data.reservas.forEach(r => {
        const startHour = parseInt(r.hora_inicio.split(":")[0]);
        const endHour = parseInt(r.hora_fin.split(":")[0]) - 1;
        let estado = "available";
        if (r.estado_pago === "Pagado") estado = "reserved";
        else if (r.estado_pago === "Parcial") estado = "partial";
        else estado = "noabono";

        for (let h = startHour; h <= endHour; h++) {
          reservas[fecha][activeCancha][h] = {
            reserva_id: r.reserva_id || null,
            cliente: r.nombre_cliente,
            celular: r.celular,
            cancha: activeCancha,
            abono: r.abono,
            costo: r.precio_total,
            estado,
            startHour,
            duracion: endHour - startHour + 1
          };
        }
      });
    }
  } catch (err) {
    console.error("❌ Error cargando reservas", err);
  }

  renderHoras(day, month, year, activeCancha);
  modal.style.display = "flex";
}

// ---------- render horas ----------
function renderHoras(day, month, year, cancha) {
  hoursGrid.innerHTML = "";
  const key = dateKey(year, month, day);
  if (!reservas[key]) reservas[key] = {};
  if (!reservas[key][cancha]) reservas[key][cancha] = {};

  const estados = reservas[key][cancha];

  for (let h = 9; h <= 23; h++) {
    const slot = document.createElement("div");
    slot.classList.add("hour");

    const reserva = estados[h];
    let estado = "available";
    if (reserva) estado = reserva.estado;

    slot.classList.add(estado);
    slot.textContent = `${h}:00`;
    if (estado === "available") {
      slot.onclick = () => openReserveModal(day, month, year, h, cancha);
    } else {
      slot.style.pointerEvents = "none";
      slot.style.opacity = "0.6";
    }

    hoursGrid.appendChild(slot);
  }
}

// ---------- pestañas ----------
tabButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    tabButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeCancha = btn.dataset.cancha;
    if (lastDay !== null) renderHoras(lastDay, lastMonth, lastYear, activeCancha);
  });
});

// ---------- abrir formulario ----------
function buildDurationOptions(startHour) {
  const maxByHour = 24 - startHour;
  const limit = Math.min(maxByHour, 12);
  duracionSelect.innerHTML = "";
  for (let i = 1; i <= limit; i++) {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = i === 1 ? "1 hora" : `${i} horas`;
    duracionSelect.appendChild(opt);
  }
}

function actualizarCostoPreview() {
  const dur = parseInt(duracionSelect.value, 10) || 1;
  let total = 0;
  for (let h = selectedHour; h < selectedHour + dur; h++) total += costoHora(h);
  costoInput.value = `S/ ${total}`;
}

function openReserveModal(day, month, year, hour, cancha) {
  selectedHour = hour;
  modal.style.display = "none";
  reserveModal.style.display = "flex";
  selectedHourText.textContent = `Reserva ${day}/${month+1}/${year} - ${hour}:00 (${cancha})`;
  buildDurationOptions(hour);
  actualizarCostoPreview();
}

duracionSelect.onchange = actualizarCostoPreview;

// ---------- guardar reserva ----------
reserveForm.onsubmit = async (e) => {
  e.preventDefault();

  const cliente = document.getElementById("cliente").value.trim();
  const celular = document.getElementById("celular").value.trim();
  const cancha  = activeCancha;
  const abono   = parseFloat(document.getElementById("abono").value) || 0;
  const duracion = parseInt(duracionSelect.value, 10) || 1;

  const key = dateKey(lastYear, lastMonth, lastDay);
  const fecha = key;
  const horaInicio = `${pad(selectedHour)}:00`;
  const horaFin = `${pad(selectedHour + duracion)}:00`;

  let costoTotal = 0;
  for (let h = selectedHour; h < selectedHour + duracion; h++) costoTotal += costoHora(h);

  const dueno_id = localStorage.getItem("dueno_id");
  if (!dueno_id) {
    alert("❌ No se encontró dueño logueado. Inicia sesión de nuevo.");
    return;
  }

  try {
    const res = await fetch("https://golcontrol-g7gkhdbbg2hbgma8.canadacentral-01.azurewebsites.net/reservar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dueno_id,
        cancha_id: cancha === "C1" ? 1 : cancha === "C2" ? 2 : 3,
        fecha,
        hora_inicio: horaInicio,
        hora_fin: horaFin,
        nombre_cliente: cliente,
        celular,
        abono,
        precio_total: costoTotal
      })
    });

    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "Error desconocido");
    alert("✅ Reserva guardada correctamente");
    await openModal(lastDay, lastMonth, lastYear);
  } catch (err) {
    alert("❌ Error al guardar: " + err.message);
  }

  reserveModal.style.display = "none";
  reserveForm.reset();
};

// ---------- historial ----------
viewDayHistory.onclick = async () => {
  const key = dateKey(lastYear, lastMonth, lastDay);
  dayHistoryTitle.textContent = `Historial ${lastDay}/${lastMonth+1}/${lastYear}`;
  dayHistoryContent.innerHTML = "";

  const dayData = reservas[key];
  if (!dayData) {
    dayHistoryContent.innerHTML = "<p>No hay reservas.</p>";
    modal.style.display = "none";
    dayHistoryModal.style.display = "flex";
    return;
  }

  const groups = {};
  Object.keys(dayData).forEach(cancha => {
    Object.values(dayData[cancha]).forEach(r => {
      if (!r || !r.reserva_id) return;
      groups[r.reserva_id] = r;
    });
  });

  Object.values(groups).forEach(g => {
    const card = document.createElement("div");
    card.className = `reserva-card ${g.estado}`;
    const rango = rangoTexto(g.startHour, g.duracion);

    card.innerHTML = `
      <p><b>⏰ Horario:</b> ${rango}</p>
      <p><b>👤 Cliente:</b> ${g.cliente}</p>
      <p><b>📞 Celular:</b> ${g.celular}</p>
      <p><b>⚽ Cancha:</b> ${g.cancha}</p>
      <p><b>💵 Costo:</b> S/${g.costo} | <b>Abono:</b> S/${g.abono}</p>
      <p><b>Estado:</b> ${estadoTexto(g.estado)}</p>
      ${g.estado !== "reserved" ? `<button class="btn-pagar" data-id="${g.reserva_id}">💰 Pagar saldo</button>` : ""}
      <button class="btn-eliminar" data-id="${g.reserva_id}">❌ Eliminar</button>
    `;
    dayHistoryContent.appendChild(card);
  });

  // Pagar saldo
  dayHistoryContent.querySelectorAll(".btn-pagar").forEach(btn => {
    btn.onclick = async () => {
      const monto = prompt("Monto del abono (S/):", "0");
      const m = parseFloat(monto || "0");
      if (m <= 0) return;

      try {
        const res = await fetch("https://golcontrol-g7gkhdbbg2hbgma8.canadacentral-01.azurewebsites.net/abonar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reserva_id: btn.dataset.id, monto_abono: m })
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "Error abonar");
        alert(`✅ Abono registrado. Total abonado: S/${data.total_abonos}`);
        await openModal(lastDay, lastMonth, lastYear);
        dayHistoryModal.style.display = "none";
      } catch (err) {
        alert("❌ " + err.message);
      }
    };
  });

  // Eliminar reserva
  dayHistoryContent.querySelectorAll(".btn-eliminar").forEach(btn => {
    btn.onclick = async () => {
      if (!confirm("¿Anular esta reserva?")) return;
      try {
        const res = await fetch("https://golcontrol-g7gkhdbbg2hbgma8.canadacentral-01.azurewebsites.net/anular_reserva", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reserva_id: btn.dataset.id })
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "Error anular");
        alert("✅ Reserva anulada correctamente");
        await openModal(lastDay, lastMonth, lastYear);
        dayHistoryModal.style.display = "none";
      } catch (err) {
        alert("❌ " + err.message);
      }
    };
  });

  modal.style.display = "none";
  dayHistoryModal.style.display = "flex";
};

// ---------- cerrar modales ----------
closeModal.onclick = () => (modal.style.display = "none");
closeReserveModal.onclick = () => (reserveModal.style.display = "none");
if (closeDayHistory) closeDayHistory.onclick = () => (dayHistoryModal.style.display = "none");

window.onclick = (e) => {
  if (e.target === modal) modal.style.display = "none";
  if (e.target === reserveModal) reserveModal.style.display = "none";
  if (e.target === dayHistoryModal) dayHistoryModal.style.display = "none";
};

// ---------- navegación ----------
document.getElementById("prev").onclick = () => {
  currentMonth--;
  if (currentMonth < 0) { currentMonth = 11; currentYear--; }
  renderCalendar(currentMonth, currentYear);
};
document.getElementById("next").onclick = () => {
  currentMonth++;
  if (currentMonth > 11) { currentMonth = 0; currentYear++; }
  renderCalendar(currentMonth, currentYear);
};

// ---------- init ----------
renderCalendar(currentMonth, currentYear);
