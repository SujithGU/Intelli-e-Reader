import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { AppService } from './services/app.service';
import { WordInfoComponent } from './components/word-info/word-info.component';
import { UtilityService } from './services/utility.service';
import { BookLayoutComponent } from './components/book-layout/book-layout.component';
import { HomeComponent } from './components/home/home.component';

@NgModule({
  declarations: [
    AppComponent,
    WordInfoComponent,
    BookLayoutComponent,
    HomeComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule
  ],
  providers: [AppService, UtilityService],
  bootstrap: [AppComponent]
})
export class AppModule { }
