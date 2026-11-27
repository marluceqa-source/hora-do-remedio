/**
 * Geração de código TOTP (RFC 6238) com a biblioteca padrão do Node.
 *
 * O portal exige autenticação em duas etapas: senha e depois um código de 6 dígitos de
 * aplicativo autenticador. Para automatizar o login de ponta a ponta a automação precisa
 * calcular esse código, e é isso que este módulo faz — mesmo algoritmo que o backend
 * valida com pyotp (HMAC-SHA1, janela de 30 segundos, 6 dígitos).
 */

const crypto = require('node:crypto');

const ALFABETO_BASE32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

/** Converte um segredo em base32 (formato do otpauth://) para bytes. */
function base32ParaBytes(segredoBase32) {
  const limpo = String(segredoBase32).toUpperCase().replace(/=+$/, '').replace(/\s+/g, '');

  let acumulador = 0;
  let bitsDisponiveis = 0;
  const bytes = [];

  for (const caractere of limpo) {
    const indice = ALFABETO_BASE32.indexOf(caractere);
    if (indice === -1) throw new Error(`Caractere inválido no segredo base32: "${caractere}"`);

    acumulador = (acumulador << 5) | indice;
    bitsDisponiveis += 5;

    if (bitsDisponiveis >= 8) {
      bytes.push((acumulador >>> (bitsDisponiveis - 8)) & 0xff);
      bitsDisponiveis -= 8;
    }
  }

  return Buffer.from(bytes);
}

/** Extrai o segredo de uma URI otpauth:// (o que o backend devolve em provisioning_uri). */
function extrairSegredoDaUri(provisioningUri) {
  const segredo = new URL(provisioningUri).searchParams.get('secret');
  if (!segredo) throw new Error(`URI de provisionamento sem o parâmetro "secret": ${provisioningUri}`);
  return segredo;
}

/** Gera o código TOTP de 6 dígitos válido no instante informado (padrão: agora). */
function gerarCodigoTotp(segredoBase32, { passoSegundos = 30, digitos = 6, agoraMs = Date.now() } = {}) {
  const contador = Math.floor(agoraMs / 1000 / passoSegundos);

  const bufferContador = Buffer.alloc(8);
  bufferContador.writeBigInt64BE(BigInt(contador));

  const hmac = crypto.createHmac('sha1', base32ParaBytes(segredoBase32)).update(bufferContador).digest();

  // Truncamento dinâmico definido na RFC 4226.
  const deslocamento = hmac[hmac.length - 1] & 0x0f;
  const valor =
    ((hmac[deslocamento] & 0x7f) << 24) |
    ((hmac[deslocamento + 1] & 0xff) << 16) |
    ((hmac[deslocamento + 2] & 0xff) << 8) |
    (hmac[deslocamento + 3] & 0xff);

  return String(valor % 10 ** digitos).padStart(digitos, '0');
}

/** Atalho: recebe a URI otpauth:// e devolve o código pronto. */
function gerarCodigoDaUri(provisioningUri, opcoes) {
  return gerarCodigoTotp(extrairSegredoDaUri(provisioningUri), opcoes);
}

module.exports = { base32ParaBytes, extrairSegredoDaUri, gerarCodigoTotp, gerarCodigoDaUri };
