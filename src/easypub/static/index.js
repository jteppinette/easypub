function initEditor() {
  const quill = new Quill('#quill', {
    modules: { toolbar: true },
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

  const content = `
    <h1>Welcome to EasyPub.io</h1>
    <p>When a reviewer wishes to give special recognition to a book, he predicts that it will still be read “a hundred years from now.” The Law, first published as a pamphlet in June, 1850, is already more than a hundred years old. And because its truths are eternal, it will still be read when another century has passed. Frederic Bastiat (1801-1850) was a French economist, statesman, and author. He did most of his writing during the years just before — and immediately following — the Revolution of February 1848. This was the period when France was rapidly turning to complete socialism. As a Deputy to the Legislative Assembly, Mr. Bastiat was studying and explaining each socialist fallacy as it appeared. And he explained how socialism must inevitably degenerate into communism. But most of his countrymen chose to ignore his logic. The Law is here presented again because the same situation exists in America today as in the France of 1848. The same socialist-communist ideas and plans that were then adopted in France are now sweeping America. The explanations and arguments then advanced against socialism by Mr. Bastiat are — word for word — equally valid today. His ideas deserve a serious hearing:</p>
    <ul>
       <li>Morbi in sem quis dui placerat ornare. Pellentesque odio nisi, euismod in, pharetra a, ultricies in, diam. Sed arcu. Cras consequat.</li>
       <li>Praesent dapibus, neque id cursus faucibus, tortor neque egestas augue, eu vulputate magna eros eu erat. Aliquam erat volutpat. Nam dui mi, tincidunt quis, accumsan porttitor, facilisis luctus, metus.</li>
       <li>Phasellus ultrices nulla quis nibh. Quisque a lectus. Donec consectetuer ligula vulputate sem tristique cursus. Nam nulla quam, gravida non, commodo a, sodales sit amet, nisi.</li>
       <li>Pellentesque fermentum dolor. Aliquam quam lectus, facilisis auctor, ultrices ut, elementum vulputate, nunc.</li>
    </ul>
  `

  quill.clipboard.dangerouslyPasteHTML(0, content)
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

const { render, html, useState, useEffect } = htmPreact

function ValidationErrorAlert(errors) {
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
  return html`
    <div class="alert alert-success">
      <span
        ><strong>Congratulations!</strong> Your post was successfully published
        to <strong><a href=${url} id="link">${url}</a></strong
        >.</span
      >
      <p>
        Please store the following secret key in a secure location. This secret
        key will be required to modify or delete your post.
      </p>
      <pre class="secret">${secret}</pre>
    </div>
  `
}

function App() {
  const [title, setTitle] = useState('')
  const [result, setResult] = useState()
  const [validationError, setValidationError] = useState()
  const [httpError, setHTTPError] = useState()
  const [isLoading, setIsLoading] = useState(false)

  const submitText = isLoading ? 'Publishing...' : 'Publish'

  const url = `${location.protocol}//${location.host}/`

  function submit(event) {
    event.preventDefault()

    setIsLoading(true)

    const content = document.getElementsByClassName('ql-editor')[0].innerHTML

    fetchjson('/api/publish', 'POST', { title, content })
      .then(({ data }) => {
        setResult(data)

        setValidationError()
        setHTTPError()
      })
      .catch(({ data, response }) => {
        if (response.status == 422) {
          setValidationError(data)
          setHTTPError()
        } else {
          setHTTPError(response.status)
          setValidationError()
        }

        setResult()
      })
      .then(() => setIsLoading(false))
  }

  return html`
    <div class="container">
      <div class="panel panel-white">
        <form onSubmit=${submit}>
          <input
            onInput=${(e) => setTitle(e.target.value)}
            value=${title}
            type="text"
            name="title"
            placeholder="Title"
          />

          ${validationError &&
          html`<${ValidationErrorAlert} ...${validationError} />`}
          ${httpError !== undefined &&
          html`<${HTTPErrorAlert} status=${httpError} />`}
          ${result && html`<${SuccessAlert} ...${result} />`}

          <button disabled=${isLoading} type="submit">${submitText}</button>
        </form>
      </div>
    </div>
  `
}

function initApp() {
  render(html`<${App} />`, document.getElementById('app'))
}

initEditor()
initApp()
