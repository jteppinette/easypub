function editor(initial) {
  const quill = new Quill('#quill', {
    modules: {
      toolbar: true,
      clipboard: { matchVisual: false }
    },
    theme: 'snow',
    keyboard: {
      bindings: {
        list: {
          key: 'backspace',
          context: { format: ['list'] },
          handler: (range, context) => {
            if (range.index === 0) return

            if (range.length === 0) {
              this.quill.deleteText(range.index - 1, 1, Quill.sources.USER)
            } else {
              this.quill.deleteText(range, Quill.sources.USER)
            }
          }
        }
      }
    }
  })

  fetch(initial)
    .then((response) => response.text())
    .then((html) => quill.clipboard.dangerouslyPasteHTML(html))

  return quill
}

function fetchjson(url, method, data) {
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }

  const body = data !== undefined && JSON.stringify(data)

  return new Promise((resolve, reject) => {
    fetch(url, { method, headers, body })
      .then((response) => {
        response
          .json()
          .then((data) => {
            if (response.ok) {
              resolve({ data, response })
            } else {
              reject({ data, response })
            }
          })
          .catch(() => {
            reject({ data: undefined, response })
          })
      })
      .catch(() => {
        reject({ data: undefined, response: Response.error() })
      })
  })
}

function ValidationErrorAlert(errors) {
  const { html } = htmPreact

  function capitalize(v) {
    return v.charAt(0).toUpperCase() + v.slice(1)
  }

  return html`
    <div class="alert alert-danger">
      <span
        >We were unable to publish your post. Resolve the following errors, then
        try again:</span
      >
      <ul>
        ${Object.entries(errors).flatMap(([key, messages]) =>
          messages.map(
            (message) => html`<li>${capitalize(key)} ${message}.</li>`
          )
        )}
      </ul>
    </div>
  `
}

function HTTPErrorAlert({ status }) {
  const { html } = htmPreact

  function message() {
    if (status == 429) {
      return 'Your publish request was throttled. You cannot publish more than 60 times an hour. Please wait, then try again.'
    } else {
      return 'We received an unexpected error and were unable to publish your post. Please wait, then try again.'
    }
  }

  return html`<div class="alert alert-danger">${message()}</div> `
}

function SuccessAlert({ url, secret }) {
  const { html } = htmPreact

  return html`
    <div class="alert alert-success">
      <span
        ><strong>Congratulations!</strong> Your post was successfully published
        to <strong><a href=${url} id="link">${url}</a></strong
        >.</span
      >
      ${secret &&
      html`
        <p>
          Please store the following secret key in a secure location. This
          secret key will be required to modify or delete your post.
        </p>
        <pre class="secret">${secret}</pre>
      `}
    </div>
  `
}
