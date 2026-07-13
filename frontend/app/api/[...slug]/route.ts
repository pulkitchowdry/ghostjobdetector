export async function OPTIONS(){
    return new Response(null, {
        status: 200,
        headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    })
}

export async function GET(req: Request) {
    return (handleProxy(req))
}

export async function POST (req: Request) {
    console.log(`Proxy received POST request`)
    return (handleProxy(req))
}

async function handleProxy(req: Request) {
    console.log(`Proxy handler`)
    const awsLambdaUrl = process.env.NEXT_PUBLIC_API_URL
    const receivedUrl = new URL(req.url)
    const path = receivedUrl?.pathname.split('/api/').pop()
    const fullLambdaUrl = `${awsLambdaUrl}/${path}`

    const response = await fetch(fullLambdaUrl,
        {
            method: req.method,
            headers: req.headers,
            body: req.method != 'GET' && req.method != 'HEAD'
                ? await req.text()
                : undefined
        }
    )

    const data = await response.text()

    return (new Response(data, {
        status: response.status,
        headers: {
            "Access-Control-Allow-Origin": "*"
        }
    }))
}
