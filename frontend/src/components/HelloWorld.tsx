import React from 'react'

interface HelloWorldProps {
  msg: string
}

const HelloWorld: React.FC<HelloWorldProps> = ({ msg }) => {
  return (
    <div className="hello">
      <h1>{msg}</h1>
      <p>
        Welcome to our CRM System
      </p>
    </div>
  )
}

export default HelloWorld