// atoms_certs.gs — atoms for professional certification study pages
// Schema for cert_disclaimer:
//   { type: 'cert_disclaimer', cert: 'TOGAF®', holder: 'The Open Group', url?: '...' }

_RENDERERS['cert_disclaimer'] = function(b) {
  var cert   = b.cert   || '';
  var holder = b.holder || '';
  var url    = b.url    || '';

  var holderLink = url
    ? '<a href="' + _esc(url) + '" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;">' + _esc(holder) + '</a>'
    : _esc(holder);

  var certRef = cert ? '<strong>' + _esc(cert) + '</strong> is a registered trademark of ' + holderLink + '. ' : '';

  return (
    '<div style="' +
      'margin:16px 0 8px;' +
      'padding:10px 14px;' +
      'border-left:3px solid rgba(148,163,184,0.3);' +
      'border-radius:0 6px 6px 0;' +
      'background:rgba(148,163,184,0.06);' +
    '">' +
      '<p style="' +
        'margin:0;' +
        'font-size:11px;' +
        'line-height:1.6;' +
        'color:rgba(148,163,184,0.75);' +
        'font-family:JetBrains Mono,monospace;' +
        'letter-spacing:0.02em;' +
      '">' +
        '© ' + holderLink + '. ' +
        certRef +
        'This study material is an independent work and is not affiliated with, endorsed by, or sponsored by ' + _esc(holder) + '. ' +
        'All trademarks remain the property of their respective holders.' +
      '</p>' +
    '</div>'
  );
};
