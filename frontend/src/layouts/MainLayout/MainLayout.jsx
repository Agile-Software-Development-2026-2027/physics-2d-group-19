import { Outlet} from 'react-router-dom'
import { Header } from '../../components/Header/Header.jsx'
import styles from './MainLayout.module.css'


export function MainLayout({backendStatus}) {
  return (
    <div className={styles.appLayout}>
      <Header backendStatus={backendStatus}>
        <span>Backend: {backendStatus}</span>
      </Header>
      <main className={styles.mainContent}>
        <Outlet/>
      </main>
    </div>
  )
}