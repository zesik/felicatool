document.addEventListener('DOMContentLoaded', function() {
  const isMac = () => navigator.platform.match(/iPad|iPod|iPhone|Mac/i);
  if (isMac()) {
    document.getElementsByTagName('body')[0].classList.add('mac');
  }

  const namespace = '/felica'
  const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
  socket.on('hardware', json => {
    if (typeof json.device !== 'undefined') {
      document.getElementById('hardware-device').innerText = json.device.product;
    }
    document.getElementById('hardware-status').innerText = json.status;
  });
  socket.on('felica', json => {
    updateCardInfo(json);
    updateHistoryRecords(json);
  });

  const formatNumber = num => num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  const createElement = (tagName, classNames, inner) => {
    const el = document.createElement(tagName);
    if (classNames) {
      classNames.split(' ').filter(v => !!v).forEach(c => el.classList.add(c));
    }
    if (Array.isArray(inner)) {
      inner.filter(v => !!v).forEach(child => el.appendChild(child));
    } else if (inner instanceof Element) {
      el.appendChild(inner);
    } else {
      el.innerText = inner || '';
    }
    return el;
  };

  const createStationElement = (station, commuter_pass, lineAlwaysVisible) => {
    if (!station) {
      return createElement('TD');
    }

    return createElement('TD', null,
      createElement('DIV', `station-info${lineAlwaysVisible ? ' line-always-visible' : ''}`, [
        createElement('SPAN', 'line', [
          createElement('SPAN', 'company-name', station.company),
          createElement('SPAN', 'line-name', station.line),
        ]),
        createElement('SPAN', 'station', [
          createElement('SPAN', 'station-name', station.station),
          commuter_pass && createElement('SPAN', 'commuter-pass', '定')
        ]),
      ])
    );
  };

  const updateCardInfo = json => {
    // Update IDm
    const idmEl = document.getElementById('card-idm');
    idmEl.innerHTML = '';
    json.idm.match(/.{2}/g).forEach(segment => {
      idmEl.appendChild(createElement('SPAN', 'data-segment', segment));
    });

    // Update card balance
    const balanceEl = document.getElementById('card-balance');
    balanceEl.innerText = formatNumber(json.balance);
  };

  const updateHistoryRecords = json => {
    const historyEl = document.getElementById('history-records').getElementsByTagName('tbody')[0];
    historyEl.innerHTML = '';

    json.history.forEach(record => {
      const rowEl = createElement('TR', record.new ? 'data-row--new' : 'data-row--old', [
        createElement('TD', 'data-tabular', record.date),
        createElement('TD', 'data-tabular visible-xl', record.time),
        createElement('TD', 'visible-lg', record.terminal),
        createElement('TD', null, record.process),
        createStationElement(record.in_station, record.commuter_pass === 'in'),
        createStationElement(record.out_station, record.commuter_pass === 'out'),
        createElement('TD', 'data-tabular data-align-right',
          (typeof record.expense === 'number' && record.expense < 0) ? formatNumber(-record.expense) : ''),
        createElement('TD', 'data-tabular data-align-right',
          (typeof record.expense === 'number' && record.expense >= 0) ? formatNumber(record.expense) : ''),
        createElement('TD', 'data-tabular data-align-right', formatNumber(record.balance)),
        createElement('TD', 'visible-xl', record.serial)
      ]);
      historyEl.appendChild(rowEl);
    });
  };
});
