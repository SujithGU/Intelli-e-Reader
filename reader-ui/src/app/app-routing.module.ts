import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { BookLayoutComponent } from './components/book-layout/book-layout.component';
import { HomeComponent } from './components/home/home.component';

const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: '/home' },
  {  path: 'book', component: BookLayoutComponent },
  {  path: 'home', component: HomeComponent },
  {  path: '**', component: HomeComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true, onSameUrlNavigation: 'reload' })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
