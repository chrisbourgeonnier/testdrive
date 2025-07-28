document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const requestedDateInput = document.getElementById('id_requested_date');
  const requestedTimeInput = document.getElementById('id_requested_time');
  const selectedSlotEl = document.getElementById('selected-slot');
  const submitButton = document.getElementById('submit-button');

  // Setup FullCalendar
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'timeGridWeek',
    allDaySlot: false,
    selectable: true,
    height: 'auto',
    slotMinTime: "09:00:00",
    slotMaxTime: "16:00:00",
    slotDuration: '01:00:00',
    businessHours: {
      daysOfWeek: [1,2,3,4,5,6], // Weekdays: Mon-Sat
      startTime: '09:00',
      endTime: '17:00',
    },
    validRange: {
      start: new Date().toISOString().split('T')[0], // Disable past dates
    },
    select: function (selectionInfo) {
      const startDate = selectionInfo.start;
      const dateStr = startDate.toISOString().split('T')[0];
      const timeStr = startDate.toTimeString().slice(0, 5); // HH:MM in 24h format

      requestedDateInput.value = dateStr;
      requestedTimeInput.value = timeStr;

      selectedSlotEl.textContent = `Selected: ${dateStr} at ${timeStr}`;
      submitButton.disabled = false;
    },
    unselectAuto: false,
    headerToolbar: {
      left: 'prev today',
      center: 'title',
      right: 'next'
    },
    nowIndicator: true,
  });

  calendar.render();
});
